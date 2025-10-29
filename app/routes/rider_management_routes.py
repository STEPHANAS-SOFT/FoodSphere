from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..schemas import OrderResponse, RiderResponse
from ..models import (
    Rider, Order, OrderStatus, RiderStatus, Vendor, User,
    RiderWallet, WalletTransaction, WalletTransactionType
)
from ..services.queries import GetRiderByIdQuery, GetRiderByIdQueryHandler


router = APIRouter(
    prefix="/rider-ops",
    tags=["rider-operations"]
)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c  # Earth's radius in kilometers


class AvailableOrderResponse(BaseModel):
    order_id: int
    vendor_name: str
    vendor_address: str
    vendor_latitude: float
    vendor_longitude: float
    delivery_address: str
    customer_name: str
    customer_phone: str
    order_total: float
    distance_to_vendor: float
    estimated_delivery_fee: float
    created_at: datetime
    items_count: int


class RiderEarningsResponse(BaseModel):
    rider_id: int
    period: str
    total_deliveries: int
    total_earnings: float
    base_delivery_fees: float
    tips_received: float
    bonuses: float
    average_per_delivery: float
    daily_breakdown: List[dict]


class ActiveDeliveryResponse(BaseModel):
    order_id: int
    customer_name: str
    customer_phone: str
    pickup_address: str
    delivery_address: str
    order_total: float
    delivery_fee: float
    current_status: str
    pickup_latitude: float
    pickup_longitude: float
    delivery_latitude: Optional[float]
    delivery_longitude: Optional[float]
    estimated_distance: float
    accepted_at: datetime


@router.get("/riders/{rider_id}/available-orders", response_model=List[AvailableOrderResponse])
async def get_available_delivery_orders(
    rider_id: int,
    max_distance: float = 15.0,  # kilometers
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get available orders for delivery within rider's range"""
    
    # Verify rider exists and is available
    rider = db.query(Rider).filter(
        and_(
            Rider.id == rider_id,
            Rider.status == RiderStatus.AVAILABLE,
            Rider.is_active == True
        )
    ).first()
    
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found or not available"
        )
    
    # Get orders ready for pickup
    available_orders = db.query(Order).join(Vendor, Order.vendor_id == Vendor.id).filter(
        Order.status == OrderStatus.READY_FOR_PICKUP,
        Order.rider_id.is_(None)  # Not yet assigned to a rider
    ).all()
    
    # Calculate distances and filter
    nearby_orders = []
    for order in available_orders:
        vendor = db.query(Vendor).filter(Vendor.id == order.vendor_id).first()
        customer = db.query(User).filter(User.id == order.user_id).first()
        
        if vendor and vendor.latitude and vendor.longitude:
            distance = calculate_distance(
                rider.current_latitude, rider.current_longitude,
                vendor.latitude, vendor.longitude
            )
            
            if distance <= max_distance:
                # Count items in order
                items_count = len(order.items) if order.items else 0
                
                # Calculate estimated delivery fee (simplified)
                base_fee = 3.50
                distance_fee = distance * 0.50
                estimated_fee = base_fee + distance_fee
                
                nearby_orders.append({
                    "order": order,
                    "vendor": vendor,
                    "customer": customer,
                    "distance": distance,
                    "items_count": items_count,
                    "estimated_fee": estimated_fee
                })
    
    # Sort by distance and limit results
    nearby_orders.sort(key=lambda x: x["distance"])
    nearby_orders = nearby_orders[:limit]
    
    # Format response
    response_orders = []
    for order_data in nearby_orders:
        order = order_data["order"]
        vendor = order_data["vendor"]
        customer = order_data["customer"]
        
        response_orders.append(AvailableOrderResponse(
            order_id=order.id,
            vendor_name=vendor.name,
            vendor_address=vendor.address,
            vendor_latitude=vendor.latitude,
            vendor_longitude=vendor.longitude,
            delivery_address=order.delivery_address,
            customer_name=customer.full_name if customer else "Unknown",
            customer_phone=customer.phone_number if customer else "Unknown",
            order_total=float(order.total_amount),
            distance_to_vendor=order_data["distance"],
            estimated_delivery_fee=order_data["estimated_fee"],
            created_at=order.created_at,
            items_count=order_data["items_count"]
        ))
    
    return response_orders


@router.post("/riders/{rider_id}/accept-order/{order_id}")
async def accept_delivery_order(
    rider_id: int,
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Accept a delivery order"""
    
    # Verify rider is available
    rider = db.query(Rider).filter(
        and_(
            Rider.id == rider_id,
            Rider.status == RiderStatus.AVAILABLE,
            Rider.is_active == True
        )
    ).first()
    
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found or not available"
        )
    
    # Verify order is available for pickup
    order = db.query(Order).filter(
        and_(
            Order.id == order_id,
            Order.status == OrderStatus.READY_FOR_PICKUP,
            Order.rider_id.is_(None)
        )
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not available for pickup"
        )
    
    # Assign rider to order
    order.rider_id = rider_id
    order.status = OrderStatus.IN_TRANSIT
    order.updated_at = datetime.utcnow()
    
    # Update rider status
    rider.status = RiderStatus.BUSY
    
    db.commit()
    
    return {
        "message": "Order accepted successfully",
        "order_id": order_id,
        "rider_id": rider_id,
        "new_status": "in_transit"
    }


@router.get("/riders/{rider_id}/current-deliveries", response_model=List[ActiveDeliveryResponse])
async def get_active_deliveries(
    rider_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get rider's current active deliveries"""
    
    # Verify rider exists
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found"
        )
    
    # Get active deliveries
    active_orders = db.query(Order).filter(
        and_(
            Order.rider_id == rider_id,
            Order.status == OrderStatus.IN_TRANSIT
        )
    ).all()
    
    deliveries = []
    for order in active_orders:
        vendor = db.query(Vendor).filter(Vendor.id == order.vendor_id).first()
        customer = db.query(User).filter(User.id == order.user_id).first()
        
        # Calculate estimated distance (simplified)
        estimated_distance = 5.0  # Would calculate from addresses
        
        # Find when order was accepted by rider
        accepted_at = order.updated_at  # Simplified
        
        deliveries.append(ActiveDeliveryResponse(
            order_id=order.id,
            customer_name=customer.full_name if customer else "Unknown",
            customer_phone=customer.phone_number if customer else "Unknown",
            pickup_address=vendor.address if vendor else "Unknown",
            delivery_address=order.delivery_address,
            order_total=float(order.total_amount),
            delivery_fee=float(order.delivery_fee) if order.delivery_fee else 3.50,
            current_status=order.status.value,
            pickup_latitude=vendor.latitude if vendor else 0.0,
            pickup_longitude=vendor.longitude if vendor else 0.0,
            delivery_latitude=customer.latitude if customer else None,
            delivery_longitude=customer.longitude if customer else None,
            estimated_distance=estimated_distance,
            accepted_at=accepted_at
        ))
    
    return deliveries


@router.post("/riders/{rider_id}/complete-delivery/{order_id}")
async def mark_delivery_complete(
    order_id: int,
    rider_id: int,
    completion_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Mark delivery as completed"""
    
    # Verify order belongs to rider and is in transit
    order = db.query(Order).filter(
        and_(
            Order.id == order_id,
            Order.rider_id == rider_id,
            Order.status == OrderStatus.IN_TRANSIT
        )
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or not assigned to this rider"
        )
    
    # Update order status
    order.status = OrderStatus.DELIVERED
    order.updated_at = datetime.utcnow()
    
    # Update rider status back to available
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if rider:
        rider.status = RiderStatus.AVAILABLE
    
    # Calculate and add delivery fee to rider wallet (simplified)
    delivery_fee = float(order.delivery_fee) if order.delivery_fee else 3.50
    rider_wallet = db.query(RiderWallet).filter(RiderWallet.rider_id == rider_id).first()
    
    if rider_wallet:
        rider_wallet.balance += delivery_fee
        
        # Create wallet transaction record
        transaction = WalletTransaction(
            wallet_type="rider",
            wallet_id=rider_wallet.id,
            transaction_type=WalletTransactionType.COMMISSION,
            amount=delivery_fee,
            description=f"Delivery fee for order #{order_id}",
            reference_id=str(order_id)
        )
        db.add(transaction)
    
    db.commit()
    
    return {
        "message": "Delivery completed successfully",
        "order_id": order_id,
        "delivery_fee_earned": delivery_fee,
        "completion_time": order.updated_at,
        "notes": completion_notes
    }


@router.get("/riders/{rider_id}/earnings", response_model=RiderEarningsResponse)
async def get_rider_earnings(
    rider_id: int,
    period_days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get rider earnings for specified period"""
    
    # Verify rider exists
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found"
        )
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get completed deliveries in period
    completed_orders = db.query(Order).filter(
        and_(
            Order.rider_id == rider_id,
            Order.status == OrderStatus.DELIVERED,
            Order.updated_at >= start_date,
            Order.updated_at <= end_date
        )
    ).all()
    
    # Calculate earnings
    total_deliveries = len(completed_orders)
    base_delivery_fees = sum(float(order.delivery_fee) if order.delivery_fee else 3.50 for order in completed_orders)
    
    # Get wallet transactions for tips and bonuses
    rider_wallet = db.query(RiderWallet).filter(RiderWallet.rider_id == rider_id).first()
    tips_and_bonuses = 0.0
    
    if rider_wallet:
        wallet_transactions = db.query(WalletTransaction).filter(
            and_(
                WalletTransaction.wallet_id == rider_wallet.id,
                WalletTransaction.transaction_type.in_([
                    WalletTransactionType.BONUS,
                    WalletTransactionType.DEPOSIT  # Tips might come as deposits
                ]),
                WalletTransaction.created_at >= start_date,
                WalletTransaction.created_at <= end_date
            )
        ).all()
        
        tips_and_bonuses = sum(float(t.amount) for t in wallet_transactions)
    
    total_earnings = base_delivery_fees + tips_and_bonuses
    average_per_delivery = total_earnings / total_deliveries if total_deliveries > 0 else 0.0
    
    # Daily breakdown
    daily_earnings = {}
    for order in completed_orders:
        date_key = order.updated_at.date().isoformat()
        delivery_fee = float(order.delivery_fee) if order.delivery_fee else 3.50
        
        if date_key not in daily_earnings:
            daily_earnings[date_key] = {"deliveries": 0, "earnings": 0.0}
        
        daily_earnings[date_key]["deliveries"] += 1
        daily_earnings[date_key]["earnings"] += delivery_fee
    
    daily_breakdown = [
        {
            "date": date,
            "deliveries": data["deliveries"],
            "earnings": data["earnings"]
        }
        for date, data in sorted(daily_earnings.items())
    ]
    
    return RiderEarningsResponse(
        rider_id=rider_id,
        period=f"Last {period_days} days",
        total_deliveries=total_deliveries,
        total_earnings=total_earnings,
        base_delivery_fees=base_delivery_fees,
        tips_received=tips_and_bonuses,  # Simplified
        bonuses=0.0,  # Would track separately
        average_per_delivery=average_per_delivery,
        daily_breakdown=daily_breakdown
    )


@router.post("/riders/{rider_id}/toggle-availability")
async def toggle_rider_availability(
    rider_id: int,
    is_available: bool,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Toggle rider availability status"""
    
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found"
        )
    
    # Check if rider has active deliveries
    active_deliveries = db.query(Order).filter(
        and_(
            Order.rider_id == rider_id,
            Order.status == OrderStatus.IN_TRANSIT
        )
    ).count()
    
    if not is_available and active_deliveries > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot go offline with active deliveries"
        )
    
    # Update rider status
    if is_available:
        rider.status = RiderStatus.AVAILABLE
    else:
        rider.status = RiderStatus.OFFLINE
    
    # Update location if provided
    if latitude is not None and longitude is not None:
        rider.current_latitude = latitude
        rider.current_longitude = longitude
    
    rider.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": f"Rider {'online' if is_available else 'offline'} successfully",
        "rider_id": rider_id,
        "status": rider.status.value,
        "active_deliveries": active_deliveries
    }


@router.get("/riders/{rider_id}/performance-stats")
async def get_rider_performance_stats(
    rider_id: int,
    period_days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get rider performance statistics"""
    
    # Verify rider exists
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found"
        )
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get all orders in period
    orders = db.query(Order).filter(
        and_(
            Order.rider_id == rider_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
    ).all()
    
    completed_orders = [o for o in orders if o.status == OrderStatus.DELIVERED]
    
    # Calculate performance metrics
    total_orders_assigned = len(orders)
    total_completed = len(completed_orders)
    completion_rate = (total_completed / total_orders_assigned * 100) if total_orders_assigned > 0 else 0
    
    # Average delivery time (simplified)
    avg_delivery_time = 25  # minutes (would calculate from actual data)
    
    # Customer ratings (simplified - would come from ratings table)
    average_rating = 4.5
    total_ratings = total_completed
    
    return {
        "rider_id": rider_id,
        "period": f"Last {period_days} days",
        "total_orders_assigned": total_orders_assigned,
        "total_completed": total_completed,
        "completion_rate": round(completion_rate, 2),
        "average_delivery_time_minutes": avg_delivery_time,
        "customer_rating": {
            "average": average_rating,
            "total_ratings": total_ratings
        },
        "performance_tier": "Gold" if completion_rate >= 95 and average_rating >= 4.5 else "Silver"
    }