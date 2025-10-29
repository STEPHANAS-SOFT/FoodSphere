from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..schemas import OrderResponse
from ..models import Order, OrderItem, Item, Vendor, User, Rider, OrderStatus
from ..services.queries import GetOrderByIdQuery, GetOrderByIdQueryHandler


router = APIRouter(
    prefix="/orders",
    tags=["enhanced-orders"]
)


class OrderCalculationItem(BaseModel):
    item_id: int
    quantity: int
    variation_id: Optional[int] = None
    addon_ids: Optional[List[int]] = []


class OrderCalculationRequest(BaseModel):
    vendor_id: int
    items: List[OrderCalculationItem]
    delivery_address_id: int
    user_id: int


class OrderCalculationResponse(BaseModel):
    subtotal: float
    delivery_fee: float
    service_fee: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    estimated_delivery_time: int  # minutes
    delivery_distance: float  # kilometers


class CouponApplication(BaseModel):
    coupon_code: str
    order_id: Optional[int] = None
    subtotal: Optional[float] = None


class CouponResponse(BaseModel):
    valid: bool
    discount_amount: float
    discount_type: str  # "percentage" or "fixed"
    message: str


class OrderCancellationRequest(BaseModel):
    reason: str
    refund_to_wallet: bool = True


class OrderRatingRequest(BaseModel):
    food_rating: int  # 1-5
    delivery_rating: int  # 1-5
    vendor_rating: int  # 1-5
    comment: Optional[str] = None
    rider_rating: Optional[int] = None  # 1-5


class DeliveryEstimate(BaseModel):
    estimated_minutes: int
    estimated_delivery_time: datetime
    preparation_time: int
    travel_time: int
    status_updates: List[str]


@router.post("/calculate-total", response_model=OrderCalculationResponse)
async def calculate_order_total(
    calculation_request: OrderCalculationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Calculate order total including all fees, taxes, and delivery costs"""
    
    # Verify vendor exists and is active
    vendor = db.query(Vendor).filter(
        Vendor.id == calculation_request.vendor_id,
        Vendor.is_active == True
    ).first()
    
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found or not active"
        )
    
    # Verify user exists
    user = db.query(User).filter(User.id == calculation_request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    subtotal = 0.0
    
    # Calculate subtotal from items
    for order_item in calculation_request.items:
        item = db.query(Item).filter(
            Item.id == order_item.item_id,
            Item.vendor_id == calculation_request.vendor_id,
            Item.is_available == True
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with ID {order_item.item_id} not found or not available"
            )
        
        item_price = float(item.price)
        
        # Add variation price if applicable
        if order_item.variation_id:
            # In a real implementation, you'd fetch variation price
            pass
        
        # Add addon prices if applicable
        if order_item.addon_ids:
            # In a real implementation, you'd fetch addon prices
            pass
        
        subtotal += item_price * order_item.quantity
    
    # Calculate fees (these would be configurable in a real system)
    delivery_fee = 2.99 if subtotal < 25.0 else 0.0  # Free delivery over $25
    service_fee = subtotal * 0.02  # 2% service fee
    tax_rate = 0.08  # 8% tax
    tax_amount = (subtotal + service_fee) * tax_rate
    
    # Calculate delivery distance and time (simplified)
    delivery_distance = 5.0  # km (would calculate from addresses)
    estimated_delivery_time = 30 + (delivery_distance * 2)  # base time + travel
    
    total_amount = subtotal + delivery_fee + service_fee + tax_amount
    
    return OrderCalculationResponse(
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        service_fee=service_fee,
        tax_amount=tax_amount,
        discount_amount=0.0,
        total_amount=total_amount,
        estimated_delivery_time=int(estimated_delivery_time),
        delivery_distance=delivery_distance
    )


@router.post("/apply-coupon", response_model=CouponResponse)
async def apply_discount_coupon(
    coupon_request: CouponApplication,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Apply and validate discount coupon"""
    
    # Simplified coupon validation (in real system, you'd have a coupons table)
    valid_coupons = {
        "WELCOME10": {"type": "percentage", "value": 10, "min_order": 20},
        "SAVE5": {"type": "fixed", "value": 5, "min_order": 15},
        "FREEDELIV": {"type": "delivery", "value": 2.99, "min_order": 0}
    }
    
    coupon_code = coupon_request.coupon_code.upper()
    
    if coupon_code not in valid_coupons:
        return CouponResponse(
            valid=False,
            discount_amount=0.0,
            discount_type="none",
            message="Invalid coupon code"
        )
    
    coupon = valid_coupons[coupon_code]
    subtotal = coupon_request.subtotal or 0.0
    
    if subtotal < coupon["min_order"]:
        return CouponResponse(
            valid=False,
            discount_amount=0.0,
            discount_type="none",
            message=f"Minimum order amount ${coupon['min_order']} required"
        )
    
    # Calculate discount
    if coupon["type"] == "percentage":
        discount_amount = subtotal * (coupon["value"] / 100)
        discount_type = "percentage"
        message = f"{coupon['value']}% discount applied"
    elif coupon["type"] == "fixed":
        discount_amount = min(coupon["value"], subtotal)
        discount_type = "fixed"
        message = f"${discount_amount} discount applied"
    else:  # delivery
        discount_amount = coupon["value"]
        discount_type = "delivery"
        message = "Free delivery applied"
    
    return CouponResponse(
        valid=True,
        discount_amount=discount_amount,
        discount_type=discount_type,
        message=message
    )


@router.get("/{order_id}/estimated-delivery", response_model=DeliveryEstimate)
async def get_delivery_estimate(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get estimated delivery time for an order"""
    
    query_handler = GetOrderByIdQueryHandler(db)
    order = query_handler.handle(GetOrderByIdQuery(order_id=order_id))
    
    # Calculate estimates based on order status
    current_time = datetime.utcnow()
    
    if order.status == OrderStatus.PENDING:
        prep_time = 20  # minutes
        travel_time = 15
        total_time = prep_time + travel_time
        status_updates = [
            "Order received",
            "Waiting for vendor confirmation",
            "Estimated preparation time: 20 minutes",
            "Estimated delivery: 35 minutes"
        ]
    elif order.status == OrderStatus.ACCEPTED:
        prep_time = 18
        travel_time = 15
        total_time = prep_time + travel_time
        status_updates = [
            "Order confirmed by vendor",
            "Preparing your order",
            "Finding delivery rider",
            "Estimated delivery: 33 minutes"
        ]
    elif order.status == OrderStatus.PREPARING:
        prep_time = 10  # remaining
        travel_time = 15
        total_time = prep_time + travel_time
        status_updates = [
            "Order is being prepared",
            "Almost ready for pickup",
            "Estimated delivery: 25 minutes"
        ]
    elif order.status == OrderStatus.READY_FOR_PICKUP:
        prep_time = 0
        travel_time = 12
        total_time = travel_time
        status_updates = [
            "Order ready for pickup",
            "Assigning delivery rider",
            "Estimated delivery: 12 minutes"
        ]
    elif order.status == OrderStatus.IN_TRANSIT:
        prep_time = 0
        travel_time = 8  # remaining
        total_time = travel_time
        status_updates = [
            "Order picked up",
            "On the way to delivery",
            "Estimated delivery: 8 minutes"
        ]
    else:
        prep_time = 0
        travel_time = 0
        total_time = 0
        status_updates = ["Order delivered"]
    
    estimated_delivery_time = current_time + timedelta(minutes=total_time)
    
    return DeliveryEstimate(
        estimated_minutes=total_time,
        estimated_delivery_time=estimated_delivery_time,
        preparation_time=prep_time,
        travel_time=travel_time,
        status_updates=status_updates
    )


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    cancellation_request: OrderCancellationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Cancel an order and process refund if applicable"""
    
    query_handler = GetOrderByIdQueryHandler(db)
    order = query_handler.handle(GetOrderByIdQuery(order_id=order_id))
    
    # Check if order can be cancelled
    if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order cannot be cancelled in current status"
        )
    
    # Calculate refund amount based on order status
    refund_percentage = 1.0  # Full refund
    
    if order.status == OrderStatus.PREPARING:
        refund_percentage = 0.8  # 80% refund if already preparing
    elif order.status in [OrderStatus.READY_FOR_PICKUP, OrderStatus.IN_TRANSIT]:
        refund_percentage = 0.5  # 50% refund if rider assigned
    
    refund_amount = float(order.total_amount) * refund_percentage
    
    # Update order status
    order.status = OrderStatus.CANCELLED
    order.updated_at = datetime.utcnow()
    db.commit()
    
    # Process refund (simplified - would integrate with payment processor)
    if cancellation_request.refund_to_wallet and refund_amount > 0:
        # In real implementation, you'd add to user wallet
        pass
    
    return {
        "message": "Order cancelled successfully",
        "refund_amount": refund_amount,
        "refund_percentage": int(refund_percentage * 100),
        "reason": cancellation_request.reason
    }


@router.get("/user/{user_id}/history", response_model=List[OrderResponse])
async def get_user_order_history(
    user_id: int,
    status_filter: Optional[OrderStatus] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get user's order history with optional status filtering"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Build query
    orders_query = db.query(Order).filter(Order.user_id == user_id)
    
    if status_filter:
        orders_query = orders_query.filter(Order.status == status_filter)
    
    # Order by most recent first
    orders = orders_query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    return orders


@router.post("/{order_id}/rate")
async def rate_order(
    order_id: int,
    rating_request: OrderRatingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Submit rating and review for a completed order"""
    
    query_handler = GetOrderByIdQueryHandler(db)
    order = query_handler.handle(GetOrderByIdQuery(order_id=order_id))
    
    # Verify order is delivered
    if order.status != OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only rate delivered orders"
        )
    
    # Validate ratings
    for rating_field, rating_value in [
        ("food_rating", rating_request.food_rating),
        ("delivery_rating", rating_request.delivery_rating),
        ("vendor_rating", rating_request.vendor_rating),
    ]:
        if rating_value < 1 or rating_value > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{rating_field} must be between 1 and 5"
            )
    
    if rating_request.rider_rating and (rating_request.rider_rating < 1 or rating_request.rider_rating > 5):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="rider_rating must be between 1 and 5"
        )
    
    # In a real implementation, you'd save ratings to a ratings table
    # For now, we'll just return success
    
    return {
        "message": "Rating submitted successfully",
        "order_id": order_id,
        "food_rating": rating_request.food_rating,
        "delivery_rating": rating_request.delivery_rating,
        "vendor_rating": rating_request.vendor_rating,
        "rider_rating": rating_request.rider_rating,
        "comment": rating_request.comment
    }