from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from decimal import Decimal

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..models import (
    User, Order, OrderStatus, UserWallet, WalletTransaction, 
    WalletTransactionType, WalletTransactionStatus
)


router = APIRouter(
    prefix="/promotions",
    tags=["promotions"]
)


class Promotion(BaseModel):
    id: str
    title: str
    description: str
    discount_type: str  # "percentage", "fixed_amount", "free_delivery"
    discount_value: float
    min_order_amount: float
    max_discount: Optional[float] = None
    valid_from: datetime
    valid_until: datetime
    usage_limit: Optional[int] = None
    used_count: int
    applicable_vendors: Optional[List[int]] = None  # None means all vendors
    is_active: bool
    terms_conditions: str


class Coupon(BaseModel):
    id: str
    code: str
    title: str
    discount_type: str
    discount_value: float
    min_order_amount: float
    max_discount: Optional[float] = None
    valid_until: datetime
    usage_limit_per_user: int
    user_usage_count: int
    is_active: bool


class LoyaltyStatus(BaseModel):
    user_id: int
    total_points: int
    tier: str  # "Bronze", "Silver", "Gold", "Platinum"
    points_to_next_tier: int
    lifetime_orders: int
    lifetime_spent: float
    available_rewards: List[dict]


class LoyaltyTransaction(BaseModel):
    id: str
    user_id: int
    points: int
    transaction_type: str  # "earned", "redeemed"
    description: str
    order_id: Optional[int] = None
    created_at: datetime


@router.get("/active", response_model=List[Promotion])
async def get_active_promotions(
    vendor_id: Optional[int] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get all active promotions, optionally filtered by vendor or user eligibility"""
    
    current_time = datetime.utcnow()
    
    # Mock promotions data (in real system, this would come from database)
    all_promotions = [
        {
            "id": "promo_welcome_2024",
            "title": "Welcome Offer",
            "description": "Get 20% off your first order",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "min_order_amount": 15.0,
            "max_discount": 10.0,
            "valid_from": current_time - timedelta(days=30),
            "valid_until": current_time + timedelta(days=30),
            "usage_limit": None,
            "used_count": 245,
            "applicable_vendors": None,  # All vendors
            "is_active": True,
            "terms_conditions": "Valid for new users only. Cannot be combined with other offers."
        },
        {
            "id": "promo_free_delivery",
            "title": "Free Delivery Weekend",
            "description": "Free delivery on orders over $25",
            "discount_type": "free_delivery",
            "discount_value": 3.99,
            "min_order_amount": 25.0,
            "max_discount": None,
            "valid_from": current_time - timedelta(days=2),
            "valid_until": current_time + timedelta(days=2),
            "usage_limit": 1000,
            "used_count": 432,
            "applicable_vendors": None,
            "is_active": True,
            "terms_conditions": "Valid on weekends only. Limited time offer."
        },
        {
            "id": "promo_lunch_special",
            "title": "Lunch Special",
            "description": "$5 off lunch orders between 11 AM - 2 PM",
            "discount_type": "fixed_amount",
            "discount_value": 5.0,
            "min_order_amount": 20.0,
            "max_discount": None,
            "valid_from": current_time - timedelta(days=7),
            "valid_until": current_time + timedelta(days=7),
            "usage_limit": None,
            "used_count": 156,
            "applicable_vendors": [1, 2, 3] if vendor_id else None,
            "is_active": True,
            "terms_conditions": "Valid Monday-Friday, 11 AM to 2 PM only."
        }
    ]
    
    # Filter by vendor if specified
    active_promotions = []
    for promo in all_promotions:
        if not promo["is_active"]:
            continue
            
        if promo["valid_until"] < current_time:
            continue
            
        if vendor_id and promo["applicable_vendors"] and vendor_id not in promo["applicable_vendors"]:
            continue
            
        # Check usage limits
        if promo["usage_limit"] and promo["used_count"] >= promo["usage_limit"]:
            continue
            
        active_promotions.append(Promotion(**promo))
    
    return active_promotions


@router.post("/validate-coupon")
async def validate_coupon_code(
    coupon_code: str,
    order_amount: float,
    user_id: int,
    vendor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Validate a coupon code and return discount details"""
    
    # Mock coupon database (in real system, stored in database)
    coupons_db = {
        "WELCOME20": {
            "id": "coup_welcome20",
            "title": "Welcome 20% Off",
            "discount_type": "percentage",
            "discount_value": 20.0,
            "min_order_amount": 15.0,
            "max_discount": 15.0,
            "valid_until": datetime.utcnow() + timedelta(days=30),
            "usage_limit_per_user": 1,
            "is_active": True
        },
        "SAVE5NOW": {
            "id": "coup_save5now",
            "title": "$5 Off Your Order",
            "discount_type": "fixed_amount",
            "discount_value": 5.0,
            "min_order_amount": 25.0,
            "max_discount": None,
            "valid_until": datetime.utcnow() + timedelta(days=14),
            "usage_limit_per_user": 3,
            "is_active": True
        },
        "FREEDELIV": {
            "id": "coup_freedeliv",
            "title": "Free Delivery",
            "discount_type": "free_delivery",
            "discount_value": 3.99,
            "min_order_amount": 20.0,
            "max_discount": None,
            "valid_until": datetime.utcnow() + timedelta(days=7),
            "usage_limit_per_user": 2,
            "is_active": True
        }
    }
    
    coupon_code_upper = coupon_code.upper()
    
    if coupon_code_upper not in coupons_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid coupon code"
        )
    
    coupon_data = coupons_db[coupon_code_upper]
    
    # Check if coupon is active
    if not coupon_data["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon is no longer active"
        )
    
    # Check expiry date
    if datetime.utcnow() > coupon_data["valid_until"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon has expired"
        )
    
    # Check minimum order amount
    if order_amount < coupon_data["min_order_amount"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum order amount ${coupon_data['min_order_amount']} required"
        )
    
    # Check user usage limit (simplified - would check from database)
    user_usage_count = 0  # Would query from coupon_usage table
    
    if user_usage_count >= coupon_data["usage_limit_per_user"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon usage limit reached for this user"
        )
    
    # Calculate discount amount
    if coupon_data["discount_type"] == "percentage":
        discount_amount = order_amount * (coupon_data["discount_value"] / 100)
        if coupon_data["max_discount"]:
            discount_amount = min(discount_amount, coupon_data["max_discount"])
    elif coupon_data["discount_type"] == "fixed_amount":
        discount_amount = min(coupon_data["discount_value"], order_amount)
    else:  # free_delivery
        discount_amount = coupon_data["discount_value"]
    
    return {
        "valid": True,
        "coupon_code": coupon_code,
        "discount_amount": discount_amount,
        "discount_type": coupon_data["discount_type"],
        "title": coupon_data["title"],
        "message": f"Coupon applied! You saved ${discount_amount:.2f}"
    }


@router.get("/users/{user_id}/coupons", response_model=List[Coupon])
async def get_user_available_coupons(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get all available coupons for a specific user"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mock user-specific coupons (in real system, would query from database)
    user_coupons = [
        {
            "id": "coup_birthday_2024",
            "code": "BIRTHDAY2024",
            "title": "Birthday Special",
            "discount_type": "percentage",
            "discount_value": 25.0,
            "min_order_amount": 30.0,
            "max_discount": 20.0,
            "valid_until": datetime.utcnow() + timedelta(days=7),
            "usage_limit_per_user": 1,
            "user_usage_count": 0,
            "is_active": True
        },
        {
            "id": "coup_loyal_customer",
            "code": "LOYAL10",
            "title": "Loyal Customer Reward",
            "discount_type": "fixed_amount",
            "discount_value": 10.0,
            "min_order_amount": 40.0,
            "max_discount": None,
            "valid_until": datetime.utcnow() + timedelta(days=30),
            "usage_limit_per_user": 2,
            "user_usage_count": 0,
            "is_active": True
        }
    ]
    
    # Filter active and non-expired coupons
    available_coupons = []
    current_time = datetime.utcnow()
    
    for coupon_data in user_coupons:
        if (coupon_data["is_active"] and 
            coupon_data["valid_until"] > current_time and
            coupon_data["user_usage_count"] < coupon_data["usage_limit_per_user"]):
            
            available_coupons.append(Coupon(**coupon_data))
    
    return available_coupons


@router.post("/loyalty/earn-points")
async def earn_loyalty_points(
    user_id: int,
    order_id: int,
    points_earned: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Award loyalty points to user for an order"""
    
    # Verify order exists and belongs to user
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id,
        Order.status == OrderStatus.DELIVERED
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or not eligible for points"
        )
    
    # Calculate points if not provided (1 point per dollar spent)
    if points_earned is None:
        points_earned = int(float(order.total_amount))
    
    # In real system, you'd update loyalty points table
    # For now, we'll simulate adding to wallet as bonus
    
    user_wallet = db.query(UserWallet).filter(UserWallet.user_id == user_id).first()
    if user_wallet:
        # Convert points to small monetary bonus (e.g., 100 points = $1)
        bonus_amount = Decimal(str(points_earned / 100))
        user_wallet.balance += bonus_amount
        
        # Create transaction record
        transaction = WalletTransaction(
            wallet_type="user",
            wallet_id=user_wallet.id,
            transaction_type=WalletTransactionType.BONUS,
            amount=bonus_amount,
            status=WalletTransactionStatus.COMPLETED,
            description=f"Loyalty points bonus: {points_earned} points for order #{order_id}",
            reference_id=f"loyalty_{order_id}"
        )
        db.add(transaction)
        db.commit()
    
    return {
        "message": "Loyalty points earned successfully",
        "user_id": user_id,
        "order_id": order_id,
        "points_earned": points_earned,
        "bonus_amount": float(bonus_amount) if user_wallet else 0.0
    }


@router.get("/users/{user_id}/loyalty-status", response_model=LoyaltyStatus)
async def get_loyalty_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get user's loyalty program status and available rewards"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's order history
    user_orders = db.query(Order).filter(
        Order.user_id == user_id,
        Order.status == OrderStatus.DELIVERED
    ).all()
    
    # Calculate loyalty metrics
    lifetime_orders = len(user_orders)
    lifetime_spent = sum(float(order.total_amount) for order in user_orders)
    
    # Calculate loyalty points (simplified - 1 point per dollar)
    total_points = int(lifetime_spent)
    
    # Determine tier based on lifetime spending
    if lifetime_spent >= 500:
        tier = "Platinum"
        points_to_next_tier = 0
    elif lifetime_spent >= 250:
        tier = "Gold"
        points_to_next_tier = int(500 - lifetime_spent)
    elif lifetime_spent >= 100:
        tier = "Silver"
        points_to_next_tier = int(250 - lifetime_spent)
    else:
        tier = "Bronze"
        points_to_next_tier = int(100 - lifetime_spent)
    
    # Available rewards based on tier
    available_rewards = []
    
    if tier in ["Silver", "Gold", "Platinum"]:
        available_rewards.append({
            "id": "free_delivery",
            "title": "Free Delivery",
            "description": "Free delivery on your next order",
            "points_required": 50,
            "available": total_points >= 50
        })
    
    if tier in ["Gold", "Platinum"]:
        available_rewards.extend([
            {
                "id": "discount_10",
                "title": "$10 Off",
                "description": "$10 discount on orders over $30",
                "points_required": 100,
                "available": total_points >= 100
            },
            {
                "id": "priority_support",
                "title": "Priority Support",
                "description": "Priority customer support access",
                "points_required": 150,
                "available": total_points >= 150
            }
        ])
    
    if tier == "Platinum":
        available_rewards.append({
            "id": "exclusive_deals",
            "title": "Exclusive Deals",
            "description": "Access to exclusive vendor deals",
            "points_required": 200,
            "available": total_points >= 200
        })
    
    return LoyaltyStatus(
        user_id=user_id,
        total_points=total_points,
        tier=tier,
        points_to_next_tier=points_to_next_tier,
        lifetime_orders=lifetime_orders,
        lifetime_spent=lifetime_spent,
        available_rewards=available_rewards
    )


@router.post("/loyalty/redeem-reward")
async def redeem_loyalty_reward(
    user_id: int,
    reward_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Redeem a loyalty reward"""
    
    # Get user's loyalty status
    loyalty_status = await get_loyalty_status(user_id, db, current_user)
    
    # Find the reward
    reward = None
    for available_reward in loyalty_status.available_rewards:
        if available_reward["id"] == reward_id:
            reward = available_reward
            break
    
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found"
        )
    
    if not reward["available"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient points for this reward"
        )
    
    # Process reward redemption
    points_to_deduct = reward["points_required"]
    
    # In real system, you'd:
    # 1. Deduct points from loyalty account
    # 2. Create redemption record
    # 3. Generate coupon or apply benefit
    
    # For simulation, we'll create a coupon code
    coupon_code = f"REWARD_{reward_id.upper()}_{user_id}"
    
    return {
        "message": "Reward redeemed successfully",
        "reward_title": reward["title"],
        "points_redeemed": points_to_deduct,
        "coupon_code": coupon_code,
        "expires_at": datetime.utcnow() + timedelta(days=30),
        "instructions": f"Use coupon code {coupon_code} at checkout to apply your reward"
    }


@router.get("/campaigns/featured")
async def get_featured_campaigns(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get featured marketing campaigns and promotions"""
    
    current_time = datetime.utcnow()
    
    # Mock featured campaigns
    campaigns = [
        {
            "id": "campaign_summer_2024",
            "title": "Summer Food Festival",
            "description": "Discover amazing deals from top restaurants",
            "image_url": "https://example.com/summer-campaign.jpg",
            "start_date": current_time - timedelta(days=5),
            "end_date": current_time + timedelta(days=10),
            "featured_vendors": [1, 2, 3],
            "discount_info": "Up to 30% off on selected items",
            "is_active": True
        },
        {
            "id": "campaign_new_users",
            "title": "New User Welcome",
            "description": "Special offers for first-time users",
            "image_url": "https://example.com/welcome-campaign.jpg",
            "start_date": current_time - timedelta(days=30),
            "end_date": current_time + timedelta(days=30),
            "featured_vendors": None,  # All vendors
            "discount_info": "20% off + Free delivery",
            "is_active": True
        }
    ]
    
    # Filter active campaigns
    active_campaigns = [
        campaign for campaign in campaigns
        if campaign["is_active"] and campaign["end_date"] > current_time
    ]
    
    return {
        "featured_campaigns": active_campaigns,
        "total_count": len(active_campaigns)
    }