from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta
from decimal import Decimal

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..schemas import OrderResponse, ItemResponse
from ..models import (
    Vendor, Order, OrderItem, Item, OrderStatus, 
    WalletTransaction, VendorWallet, User
)
from ..services.queries import GetVendorByIdQuery, GetVendorByIdQueryHandler


router = APIRouter(
    prefix="/vendor-dashboard",
    tags=["vendor-dashboard"]
)


class VendorDashboardStats(BaseModel):
    total_orders_today: int
    total_revenue_today: float
    pending_orders: int
    active_orders: int  # preparing + ready for pickup
    completed_orders_today: int
    average_order_value: float
    total_items_sold_today: int
    vendor_rating: float
    wallet_balance: float


class OrderManagementResponse(BaseModel):
    order_id: int
    customer_name: str
    customer_phone: str
    order_total: float
    order_status: str
    created_at: datetime
    items_count: int
    estimated_prep_time: int
    delivery_address: str


class MenuItemStats(BaseModel):
    item_id: int
    item_name: str
    total_orders: int
    total_quantity_sold: int
    total_revenue: float
    is_available: bool
    current_price: float
    last_ordered: Optional[datetime]


class VendorAnalytics(BaseModel):
    date_range: str
    total_orders: int
    total_revenue: float
    average_order_value: float
    top_selling_items: List[MenuItemStats]
    daily_order_counts: List[dict]
    hourly_order_distribution: List[dict]
    order_status_distribution: dict


class BulkPriceUpdate(BaseModel):
    item_updates: List[dict]  # [{"item_id": 1, "new_price": 15.99}]
    percentage_change: Optional[float] = None  # Apply percentage change to all items


@router.get("/vendors/{vendor_id}/dashboard", response_model=VendorDashboardStats)
async def get_vendor_dashboard(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get vendor dashboard overview with key metrics"""
    
    # Verify vendor exists
    query_handler = GetVendorByIdQueryHandler(db)
    vendor = query_handler.handle(GetVendorByIdQuery(vendor_id=vendor_id))
    
    # Get today's date range
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Get today's orders
    today_orders = db.query(Order).filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.created_at >= today_start,
            Order.created_at < today_end
        )
    ).all()
    
    # Calculate metrics
    total_orders_today = len(today_orders)
    
    # Revenue calculation
    completed_orders_today = [o for o in today_orders if o.status == OrderStatus.DELIVERED]
    total_revenue_today = sum(float(order.total_amount) for order in completed_orders_today)
    
    # Pending and active orders
    pending_orders = db.query(Order).filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.status == OrderStatus.PENDING
        )
    ).count()
    
    active_orders = db.query(Order).filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.status.in_([OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.READY_FOR_PICKUP])
        )
    ).count()
    
    # Average order value
    average_order_value = total_revenue_today / len(completed_orders_today) if completed_orders_today else 0.0
    
    # Total items sold today
    total_items_sold = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.status == OrderStatus.DELIVERED,
            Order.created_at >= today_start,
            Order.created_at < today_end
        )
    ).scalar() or 0
    
    # Vendor rating (simplified - would be calculated from actual reviews)
    vendor_rating = 4.5  # Placeholder
    
    # Wallet balance
    vendor_wallet = db.query(VendorWallet).filter(VendorWallet.vendor_id == vendor_id).first()
    wallet_balance = float(vendor_wallet.balance) if vendor_wallet else 0.0
    
    return VendorDashboardStats(
        total_orders_today=total_orders_today,
        total_revenue_today=total_revenue_today,
        pending_orders=pending_orders,
        active_orders=active_orders,
        completed_orders_today=len(completed_orders_today),
        average_order_value=average_order_value,
        total_items_sold_today=int(total_items_sold),
        vendor_rating=vendor_rating,
        wallet_balance=wallet_balance
    )


@router.get("/vendors/{vendor_id}/orders/pending", response_model=List[OrderManagementResponse])
async def get_pending_orders(
    vendor_id: int,
    status_filter: Optional[OrderStatus] = OrderStatus.PENDING,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get vendor's pending orders for management"""
    
    # Verify vendor exists
    query_handler = GetVendorByIdQueryHandler(db)
    vendor = query_handler.handle(GetVendorByIdQuery(vendor_id=vendor_id))
    
    # Get orders
    orders_query = db.query(Order).filter(Order.vendor_id == vendor_id)
    
    if status_filter:
        orders_query = orders_query.filter(Order.status == status_filter)
    else:
        # Get all active orders if no filter
        orders_query = orders_query.filter(
            Order.status.in_([
                OrderStatus.PENDING, 
                OrderStatus.ACCEPTED, 
                OrderStatus.PREPARING, 
                OrderStatus.READY_FOR_PICKUP
            ])
        )
    
    orders = orders_query.order_by(Order.created_at.asc()).limit(limit).all()
    
    # Format response
    order_responses = []
    for order in orders:
        # Get customer info
        customer = db.query(User).filter(User.id == order.user_id).first()
        
        # Count items in order
        items_count = db.query(OrderItem).filter(OrderItem.order_id == order.id).count()
        
        # Estimate prep time based on items (simplified)
        estimated_prep_time = max(15, items_count * 3)  # 3 minutes per item, minimum 15
        
        order_responses.append(OrderManagementResponse(
            order_id=order.id,
            customer_name=customer.full_name if customer else "Unknown",
            customer_phone=customer.phone_number if customer else "Unknown",
            order_total=float(order.total_amount),
            order_status=order.status.value,
            created_at=order.created_at,
            items_count=items_count,
            estimated_prep_time=estimated_prep_time,
            delivery_address=order.delivery_address
        ))
    
    return order_responses


@router.post("/vendors/{vendor_id}/orders/{order_id}/accept")
async def accept_order(
    vendor_id: int,
    order_id: int,
    estimated_prep_time: Optional[int] = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Accept a pending order"""
    
    # Verify vendor owns this order
    order = db.query(Order).filter(
        and_(
            Order.id == order_id,
            Order.vendor_id == vendor_id,
            Order.status == OrderStatus.PENDING
        )
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or not in pending status"
        )
    
    # Update order status
    order.status = OrderStatus.ACCEPTED
    order.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Order accepted successfully",
        "order_id": order_id,
        "estimated_prep_time": estimated_prep_time,
        "new_status": "accepted"
    }


@router.post("/vendors/{vendor_id}/orders/{order_id}/reject")
async def reject_order(
    vendor_id: int,
    order_id: int,
    rejection_reason: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Reject a pending order"""
    
    # Verify vendor owns this order
    order = db.query(Order).filter(
        and_(
            Order.id == order_id,
            Order.vendor_id == vendor_id,
            Order.status == OrderStatus.PENDING
        )
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or not in pending status"
        )
    
    # Update order status
    order.status = OrderStatus.REJECTED
    order.updated_at = datetime.utcnow()
    
    db.commit()
    
    # In real implementation, you'd:
    # 1. Refund the customer
    # 2. Send notification
    # 3. Log the rejection reason
    
    return {
        "message": "Order rejected successfully",
        "order_id": order_id,
        "rejection_reason": rejection_reason,
        "new_status": "rejected"
    }


@router.put("/vendors/{vendor_id}/status")
async def toggle_vendor_availability(
    vendor_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Toggle vendor online/offline status"""
    
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    vendor.is_active = is_active
    vendor.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"Vendor {'activated' if is_active else 'deactivated'} successfully",
        "vendor_id": vendor_id,
        "is_active": is_active
    }


@router.get("/vendors/{vendor_id}/analytics", response_model=VendorAnalytics)
async def get_sales_analytics(
    vendor_id: int,
    days_back: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get vendor sales analytics and performance metrics"""
    
    # Verify vendor exists
    query_handler = GetVendorByIdQueryHandler(db)
    vendor = query_handler.handle(GetVendorByIdQuery(vendor_id=vendor_id))
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Get orders in date range
    orders = db.query(Order).filter(
        and_(
            Order.vendor_id == vendor_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
    ).all()
    
    # Basic metrics
    total_orders = len(orders)
    completed_orders = [o for o in orders if o.status == OrderStatus.DELIVERED]
    total_revenue = sum(float(order.total_amount) for order in completed_orders)
    average_order_value = total_revenue / len(completed_orders) if completed_orders else 0.0
    
    # Top selling items
    item_stats = db.query(
        Item.id,
        Item.name,
        Item.price,
        Item.is_available,
        func.count(OrderItem.id).label('order_count'),
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.subtotal).label('total_revenue'),
        func.max(Order.created_at).label('last_ordered')
    ).join(OrderItem, Item.id == OrderItem.item_id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(
         and_(
             Item.vendor_id == vendor_id,
             Order.created_at >= start_date,
             Order.created_at <= end_date,
             Order.status == OrderStatus.DELIVERED
         )
     ).group_by(Item.id, Item.name, Item.price, Item.is_available)\
      .order_by(func.sum(OrderItem.quantity).desc())\
      .limit(10).all()
    
    top_selling_items = [
        MenuItemStats(
            item_id=stat.id,
            item_name=stat.name,
            total_orders=stat.order_count,
            total_quantity_sold=stat.total_quantity or 0,
            total_revenue=float(stat.total_revenue or 0),
            is_available=stat.is_available,
            current_price=float(stat.price),
            last_ordered=stat.last_ordered
        ) for stat in item_stats
    ]
    
    # Daily order counts
    daily_orders = {}
    for order in completed_orders:
        date_key = order.created_at.date().isoformat()
        daily_orders[date_key] = daily_orders.get(date_key, 0) + 1
    
    daily_order_counts = [
        {"date": date, "orders": count} 
        for date, count in sorted(daily_orders.items())
    ]
    
    # Hourly distribution
    hourly_orders = {}
    for order in completed_orders:
        hour = order.created_at.hour
        hourly_orders[hour] = hourly_orders.get(hour, 0) + 1
    
    hourly_distribution = [
        {"hour": hour, "orders": hourly_orders.get(hour, 0)}
        for hour in range(24)
    ]
    
    # Order status distribution
    status_counts = {}
    for order in orders:
        status = order.status.value
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return VendorAnalytics(
        date_range=f"{start_date.date()} to {end_date.date()}",
        total_orders=total_orders,
        total_revenue=total_revenue,
        average_order_value=average_order_value,
        top_selling_items=top_selling_items,
        daily_order_counts=daily_order_counts,
        hourly_order_distribution=hourly_distribution,
        order_status_distribution=status_counts
    )


@router.post("/vendors/{vendor_id}/items/{item_id}/toggle-availability")
async def toggle_item_availability(
    vendor_id: int,
    item_id: int,
    is_available: bool,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Toggle menu item availability"""
    
    # Verify item belongs to vendor
    item = db.query(Item).filter(
        and_(
            Item.id == item_id,
            Item.vendor_id == vendor_id
        )
    ).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or doesn't belong to vendor"
        )
    
    item.is_available = is_available
    item.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"Item {'enabled' if is_available else 'disabled'} successfully",
        "item_id": item_id,
        "item_name": item.name,
        "is_available": is_available
    }


@router.post("/vendors/{vendor_id}/bulk-update-prices")
async def bulk_update_menu_prices(
    vendor_id: int,
    price_updates: BulkPriceUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Bulk update menu item prices"""
    
    # Verify vendor exists
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    updated_items = []
    
    if price_updates.percentage_change is not None:
        # Apply percentage change to all vendor items
        items = db.query(Item).filter(Item.vendor_id == vendor_id).all()
        
        for item in items:
            old_price = float(item.price)
            new_price = old_price * (1 + price_updates.percentage_change / 100)
            item.price = Decimal(str(round(new_price, 2)))
            item.updated_at = datetime.utcnow()
            
            updated_items.append({
                "item_id": item.id,
                "item_name": item.name,
                "old_price": old_price,
                "new_price": float(item.price)
            })
    
    else:
        # Apply individual item updates
        for update in price_updates.item_updates:
            item = db.query(Item).filter(
                and_(
                    Item.id == update["item_id"],
                    Item.vendor_id == vendor_id
                )
            ).first()
            
            if item:
                old_price = float(item.price)
                item.price = Decimal(str(update["new_price"]))
                item.updated_at = datetime.utcnow()
                
                updated_items.append({
                    "item_id": item.id,
                    "item_name": item.name,
                    "old_price": old_price,
                    "new_price": float(item.price)
                })
    
    db.commit()
    
    return {
        "message": f"Successfully updated {len(updated_items)} items",
        "updated_items": updated_items
    }


@router.get("/vendors/{vendor_id}/low-stock-items")
async def get_low_stock_alerts(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get items that may need attention (low stock simulation)"""
    
    # Verify vendor exists
    query_handler = GetVendorByIdQueryHandler(db)
    vendor = query_handler.handle(GetVendorByIdQuery(vendor_id=vendor_id))
    
    # In a real system, you'd track inventory
    # For now, we'll simulate based on recent order frequency
    
    # Get items with high recent orders (suggesting low stock)
    recent_date = datetime.utcnow() - timedelta(days=7)
    
    high_demand_items = db.query(
        Item.id,
        Item.name,
        Item.price,
        Item.is_available,
        func.count(OrderItem.id).label('recent_orders'),
        func.sum(OrderItem.quantity).label('total_ordered')
    ).join(OrderItem, Item.id == OrderItem.item_id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(
         and_(
             Item.vendor_id == vendor_id,
             Order.created_at >= recent_date,
             Order.status.in_([OrderStatus.DELIVERED, OrderStatus.IN_TRANSIT])
         )
     ).group_by(Item.id, Item.name, Item.price, Item.is_available)\
      .having(func.count(OrderItem.id) > 5)\
      .all()
    
    alerts = []
    for item_stat in high_demand_items:
        alerts.append({
            "item_id": item_stat.id,
            "item_name": item_stat.name,
            "current_price": float(item_stat.price),
            "is_available": item_stat.is_available,
            "recent_orders": item_stat.recent_orders,
            "total_ordered": item_stat.total_ordered,
            "alert_type": "high_demand",
            "message": f"High demand item: {item_stat.recent_orders} orders in last 7 days"
        })
    
    return {
        "vendor_id": vendor_id,
        "alerts_count": len(alerts),
        "alerts": alerts
    }