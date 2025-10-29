from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
from decimal import Decimal

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..models import (
    User, Vendor, Rider, Order, OrderItem, Item, OrderStatus,
    RiderStatus, VendorWallet, UserWallet, RiderWallet, WalletTransaction
)


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


class AdminDashboardStats(BaseModel):
    total_users: int
    total_vendors: int
    total_riders: int
    total_orders_today: int
    total_revenue_today: float
    active_orders: int
    platform_commission_today: float
    growth_metrics: Dict[str, float]


class SalesReport(BaseModel):
    period: str
    total_orders: int
    total_revenue: float
    total_commission: float
    average_order_value: float
    top_performing_vendors: List[Dict[str, Any]]
    order_trends: List[Dict[str, Any]]
    revenue_breakdown: Dict[str, float]


class VendorPerformance(BaseModel):
    vendor_id: int
    vendor_name: str
    total_orders: int
    total_revenue: float
    average_order_value: float
    completion_rate: float
    average_rating: float
    performance_score: float
    rank: int


class RiderPerformance(BaseModel):
    rider_id: int
    rider_name: str
    total_deliveries: int
    completion_rate: float
    average_delivery_time: float
    total_earnings: float
    customer_rating: float
    performance_score: float
    rank: int


@router.get("/admin/dashboard", response_model=AdminDashboardStats)
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get comprehensive admin dashboard statistics"""
    
    # Get current date ranges
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    last_month_start = today_start - timedelta(days=30)
    
    # Basic counts
    total_users = db.query(User).count()
    total_vendors = db.query(Vendor).count()
    total_riders = db.query(Rider).count()
    
    # Today's metrics
    today_orders = db.query(Order).filter(
        and_(
            Order.created_at >= today_start,
            Order.created_at < today_end
        )
    ).all()
    
    total_orders_today = len(today_orders)
    
    # Calculate today's revenue (completed orders only)
    completed_today = [o for o in today_orders if o.status == OrderStatus.DELIVERED]
    total_revenue_today = sum(float(order.total_amount) for order in completed_today)
    
    # Platform commission (5% of revenue)
    platform_commission_today = total_revenue_today * 0.05
    
    # Active orders count
    active_orders = db.query(Order).filter(
        Order.status.in_([
            OrderStatus.PENDING,
            OrderStatus.ACCEPTED,
            OrderStatus.PREPARING,
            OrderStatus.READY_FOR_PICKUP,
            OrderStatus.IN_TRANSIT
        ])
    ).count()
    
    # Growth metrics (compare with last month)
    last_month_orders = db.query(Order).filter(
        and_(
            Order.created_at >= last_month_start,
            Order.created_at < today_start
        )
    ).count()
    
    last_month_users = db.query(User).filter(
        User.created_at < today_start
    ).count()
    
    user_growth = ((total_users - last_month_users) / last_month_users * 100) if last_month_users > 0 else 0
    order_growth = ((total_orders_today - (last_month_orders / 30)) / (last_month_orders / 30) * 100) if last_month_orders > 0 else 0
    
    growth_metrics = {
        "user_growth_percentage": round(user_growth, 2),
        "order_growth_percentage": round(order_growth, 2),
        "revenue_growth_percentage": 15.3  # Placeholder
    }
    
    return AdminDashboardStats(
        total_users=total_users,
        total_vendors=total_vendors,
        total_riders=total_riders,
        total_orders_today=total_orders_today,
        total_revenue_today=total_revenue_today,
        active_orders=active_orders,
        platform_commission_today=platform_commission_today,
        growth_metrics=growth_metrics
    )


@router.get("/sales-report", response_model=SalesReport)
async def generate_sales_report(
    period_days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Generate comprehensive sales report"""
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get orders in period
    orders = db.query(Order).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date
        )
    ).all()
    
    completed_orders = [o for o in orders if o.status == OrderStatus.DELIVERED]
    
    # Basic metrics
    total_orders = len(completed_orders)
    total_revenue = sum(float(order.total_amount) for order in completed_orders)
    total_commission = total_revenue * 0.05  # 5% platform commission
    average_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Top performing vendors
    vendor_performance = db.query(
        Vendor.id,
        Vendor.name,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_amount).label('total_revenue'),
        func.avg(Order.total_amount).label('avg_order_value')
    ).join(Order, Vendor.id == Order.vendor_id).filter(
        and_(
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status == OrderStatus.DELIVERED
        )
    ).group_by(Vendor.id, Vendor.name).order_by(
        desc(func.sum(Order.total_amount))
    ).limit(10).all()
    
    top_vendors = []
    for vendor in vendor_performance:
        top_vendors.append({
            "vendor_id": vendor.id,
            "vendor_name": vendor.name,
            "total_orders": vendor.order_count,
            "total_revenue": float(vendor.total_revenue),
            "average_order_value": float(vendor.avg_order_value)
        })
    
    # Order trends (daily)
    order_trends = []
    for i in range(period_days):
        date = start_date + timedelta(days=i)
        date_end = date + timedelta(days=1)
        
        daily_orders = [o for o in completed_orders if date <= o.created_at < date_end]
        daily_count = len(daily_orders)
        daily_revenue = sum(float(order.total_amount) for order in daily_orders)
        
        order_trends.append({
            "date": date.strftime("%Y-%m-%d"),
            "orders": daily_count,
            "revenue": daily_revenue
        })
    
    # Revenue breakdown
    delivery_revenue = sum(float(order.delivery_fee or 0) for order in completed_orders)
    food_revenue = total_revenue - delivery_revenue
    
    revenue_breakdown = {
        "food_revenue": food_revenue,
        "delivery_revenue": delivery_revenue,
        "platform_commission": total_commission,
        "vendor_earnings": total_revenue - total_commission
    }
    
    return SalesReport(
        period=f"Last {period_days} days",
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_commission=total_commission,
        average_order_value=average_order_value,
        top_performing_vendors=top_vendors,
        order_trends=order_trends,
        revenue_breakdown=revenue_breakdown
    )


@router.get("/vendor-performance", response_model=List[VendorPerformance])
async def get_vendor_performance_metrics(
    period_days: int = 30,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get vendor performance rankings and metrics"""
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get vendor performance data
    vendor_stats = db.query(
        Vendor.id,
        Vendor.name,
        func.count(Order.id).label('total_orders'),
        func.sum(Order.total_amount).label('total_revenue'),
        func.avg(Order.total_amount).label('avg_order_value'),
        func.count(func.case([(Order.status == OrderStatus.DELIVERED, 1)])).label('completed_orders'),
        func.count(func.case([(Order.status == OrderStatus.CANCELLED, 1)])).label('cancelled_orders')
    ).outerjoin(Order, and_(
        Vendor.id == Order.vendor_id,
        Order.created_at >= start_date,
        Order.created_at <= end_date
    )).group_by(Vendor.id, Vendor.name).all()
    
    vendor_performances = []
    
    for i, vendor_stat in enumerate(vendor_stats):
        if vendor_stat.total_orders == 0:
            continue
            
        total_orders = vendor_stat.total_orders or 0
        completed_orders = vendor_stat.completed_orders or 0
        cancelled_orders = vendor_stat.cancelled_orders or 0
        
        # Calculate completion rate
        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        
        # Calculate performance score (weighted)
        revenue_score = min(float(vendor_stat.total_revenue or 0) / 1000, 100)  # Max 100 for $1000+
        order_score = min(total_orders * 2, 100)  # Max 100 for 50+ orders
        completion_score = completion_rate
        
        performance_score = (revenue_score * 0.4 + order_score * 0.3 + completion_score * 0.3)
        
        vendor_performances.append({
            "vendor_id": vendor_stat.id,
            "vendor_name": vendor_stat.name,
            "total_orders": total_orders,
            "total_revenue": float(vendor_stat.total_revenue or 0),
            "average_order_value": float(vendor_stat.avg_order_value or 0),
            "completion_rate": completion_rate,
            "average_rating": 4.3,  # Placeholder - would calculate from reviews
            "performance_score": performance_score
        })
    
    # Sort by performance score and add ranks
    vendor_performances.sort(key=lambda x: x["performance_score"], reverse=True)
    
    performance_results = []
    for i, vendor in enumerate(vendor_performances[:limit]):
        performance_results.append(VendorPerformance(
            **vendor,
            rank=i + 1
        ))
    
    return performance_results


@router.get("/rider-performance", response_model=List[RiderPerformance])
async def get_rider_performance_metrics(
    period_days: int = 30,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get rider performance rankings and metrics"""
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get rider performance data
    rider_stats = db.query(
        Rider.id,
        Rider.full_name,
        func.count(Order.id).label('total_deliveries'),
        func.count(func.case([(Order.status == OrderStatus.DELIVERED, 1)])).label('completed_deliveries'),
        func.sum(Order.delivery_fee).label('total_earnings')
    ).outerjoin(Order, and_(
        Rider.id == Order.rider_id,
        Order.created_at >= start_date,
        Order.created_at <= end_date
    )).group_by(Rider.id, Rider.full_name).all()
    
    rider_performances = []
    
    for rider_stat in rider_stats:
        if rider_stat.total_deliveries == 0:
            continue
            
        total_deliveries = rider_stat.total_deliveries or 0
        completed_deliveries = rider_stat.completed_deliveries or 0
        
        # Calculate completion rate
        completion_rate = (completed_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
        
        # Calculate performance score
        delivery_score = min(total_deliveries * 2, 100)  # Max 100 for 50+ deliveries
        completion_score = completion_rate
        rating_score = 85  # Placeholder - would calculate from customer ratings
        
        performance_score = (delivery_score * 0.4 + completion_score * 0.35 + rating_score * 0.25)
        
        rider_performances.append({
            "rider_id": rider_stat.id,
            "rider_name": rider_stat.full_name,
            "total_deliveries": total_deliveries,
            "completion_rate": completion_rate,
            "average_delivery_time": 22.5,  # Placeholder - would calculate actual times
            "total_earnings": float(rider_stat.total_earnings or 0),
            "customer_rating": 4.4,  # Placeholder
            "performance_score": performance_score
        })
    
    # Sort by performance score and add ranks
    rider_performances.sort(key=lambda x: x["performance_score"], reverse=True)
    
    performance_results = []
    for i, rider in enumerate(rider_performances[:limit]):
        performance_results.append(RiderPerformance(
            **rider,
            rank=i + 1
        ))
    
    return performance_results


@router.get("/popular-items")
async def get_popular_items_report(
    period_days: int = 30,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get popular menu items report"""
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get popular items
    popular_items = db.query(
        Item.id,
        Item.name,
        Item.price,
        Vendor.name.label('vendor_name'),
        func.count(OrderItem.id).label('order_count'),
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.subtotal).label('total_revenue')
    ).join(OrderItem, Item.id == OrderItem.item_id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .join(Vendor, Item.vendor_id == Vendor.id)\
     .filter(
         and_(
             Order.created_at >= start_date,
             Order.created_at <= end_date,
             Order.status == OrderStatus.DELIVERED
         )
     ).group_by(Item.id, Item.name, Item.price, Vendor.name)\
      .order_by(desc(func.sum(OrderItem.quantity)))\
      .limit(limit).all()
    
    popular_items_data = []
    for i, item in enumerate(popular_items):
        popular_items_data.append({
            "rank": i + 1,
            "item_id": item.id,
            "item_name": item.name,
            "vendor_name": item.vendor_name,
            "price": float(item.price),
            "times_ordered": item.order_count,
            "total_quantity_sold": item.total_quantity,
            "total_revenue": float(item.total_revenue),
            "average_quantity_per_order": round(item.total_quantity / item.order_count, 2)
        })
    
    return {
        "period": f"Last {period_days} days",
        "popular_items": popular_items_data,
        "total_items_analyzed": len(popular_items_data)
    }


@router.get("/financial-overview")
async def get_financial_overview(
    period_days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get comprehensive financial overview"""
    
    # Date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get wallet balances
    total_user_wallet_balance = db.query(func.sum(UserWallet.balance)).scalar() or 0
    total_vendor_wallet_balance = db.query(func.sum(VendorWallet.balance)).scalar() or 0
    total_rider_wallet_balance = db.query(func.sum(RiderWallet.balance)).scalar() or 0
    
    # Get transaction volumes
    period_transactions = db.query(WalletTransaction).filter(
        and_(
            WalletTransaction.created_at >= start_date,
            WalletTransaction.created_at <= end_date
        )
    ).all()
    
    # Calculate transaction metrics
    total_transaction_volume = sum(float(t.amount) for t in period_transactions)
    deposit_volume = sum(float(t.amount) for t in period_transactions if t.transaction_type.value == "deposit")
    payment_volume = sum(float(t.amount) for t in period_transactions if t.transaction_type.value == "payment")
    withdrawal_volume = sum(float(t.amount) for t in period_transactions if t.transaction_type.value == "withdrawal")
    
    # Platform revenue (commissions)
    commission_revenue = payment_volume * 0.05  # 5% commission
    
    return {
        "period": f"Last {period_days} days",
        "wallet_balances": {
            "total_user_balance": float(total_user_wallet_balance),
            "total_vendor_balance": float(total_vendor_wallet_balance),
            "total_rider_balance": float(total_rider_wallet_balance),
            "combined_balance": float(total_user_wallet_balance + total_vendor_wallet_balance + total_rider_wallet_balance)
        },
        "transaction_metrics": {
            "total_volume": total_transaction_volume,
            "deposit_volume": deposit_volume,
            "payment_volume": payment_volume,
            "withdrawal_volume": withdrawal_volume,
            "transaction_count": len(period_transactions)
        },
        "revenue_metrics": {
            "platform_commission_earned": commission_revenue,
            "processing_fees_collected": payment_volume * 0.029,  # 2.9% processing fees
            "total_platform_revenue": commission_revenue + (payment_volume * 0.029)
        }
    }


@router.get("/growth-trends")
async def get_growth_trends(
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get platform growth trends over time"""
    
    # Get data for last 12 months
    months_data = []
    current_date = datetime.utcnow()
    
    for i in range(12):
        # Calculate month boundaries
        month_end = current_date.replace(day=1) - timedelta(days=i*30)
        month_start = month_end - timedelta(days=30)
        
        # Count users, vendors, riders joined in this month
        users_joined = db.query(User).filter(
            and_(
                User.created_at >= month_start,
                User.created_at < month_end
            )
        ).count()
        
        vendors_joined = db.query(Vendor).filter(
            and_(
                Vendor.created_at >= month_start,
                Vendor.created_at < month_end
            )
        ).count()
        
        riders_joined = db.query(Rider).filter(
            and_(
                Rider.created_at >= month_start,
                Rider.created_at < month_end
            )
        ).count()
        
        # Count orders in this month
        orders_count = db.query(Order).filter(
            and_(
                Order.created_at >= month_start,
                Order.created_at < month_end,
                Order.status == OrderStatus.DELIVERED
            )
        ).count()
        
        # Calculate revenue
        month_orders = db.query(Order).filter(
            and_(
                Order.created_at >= month_start,
                Order.created_at < month_end,
                Order.status == OrderStatus.DELIVERED
            )
        ).all()
        
        revenue = sum(float(order.total_amount) for order in month_orders)
        
        months_data.append({
            "month": month_start.strftime("%Y-%m"),
            "users_joined": users_joined,
            "vendors_joined": vendors_joined,
            "riders_joined": riders_joined,
            "orders_completed": orders_count,
            "revenue": revenue
        })
    
    # Reverse to get chronological order
    months_data.reverse()
    
    return {
        "growth_data": months_data,
        "summary": {
            "total_months": 12,
            "avg_monthly_users": sum(m["users_joined"] for m in months_data) / 12,
            "avg_monthly_orders": sum(m["orders_completed"] for m in months_data) / 12,
            "avg_monthly_revenue": sum(m["revenue"] for m in months_data) / 12
        }
    }