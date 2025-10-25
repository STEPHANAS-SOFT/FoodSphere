from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..schemas import (
    OrderTrackingCreate,
    OrderTrackingResponse
)
from ..services.commands import (
    CreateOrderTrackingCommand,
    CreateOrderTrackingHandler,
    DeleteOrderTrackingCommand,
    DeleteOrderTrackingHandler
)
from ..services.queries import (
    GetOrderTrackingQuery,
    GetSingleOrderTrackingQuery,
    GetLatestOrderStatusQuery
)

router = APIRouter(
    prefix="/order-tracking",
    tags=["order-tracking"]
)


@router.post("/", response_model=OrderTrackingResponse)
async def create_order_tracking(
    tracking: OrderTrackingCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Create a new order tracking record"""
    command = CreateOrderTrackingCommand(
        order_id=tracking.order_id,
        status=tracking.status,
        latitude=tracking.latitude,
        longitude=tracking.longitude
    )
    
    handler = CreateOrderTrackingHandler(db)
    new_tracking = handler.handle(command)
    return new_tracking


@router.get("/", response_model=List[OrderTrackingResponse])
async def get_order_tracking(
    order_id: Optional[int] = Query(None, description="Filter by order ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get order tracking records with optional filtering"""
    query_handler = GetOrderTrackingQuery(db)
    tracking_records = query_handler.handle(order_id=order_id, skip=skip, limit=limit)
    return tracking_records


@router.get("/{tracking_id}", response_model=OrderTrackingResponse)
async def get_single_order_tracking(
    tracking_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get a specific order tracking record by ID"""
    query_handler = GetSingleOrderTrackingQuery(db)
    tracking = query_handler.handle(tracking_id)
    return tracking


@router.get("/order/{order_id}/latest", response_model=OrderTrackingResponse)
async def get_latest_order_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get the latest tracking status for a specific order"""
    query_handler = GetLatestOrderStatusQuery(db)
    latest_status = query_handler.handle(order_id)
    return latest_status


@router.delete("/{tracking_id}")
async def delete_order_tracking(
    tracking_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Delete an order tracking record"""
    command = DeleteOrderTrackingCommand(order_tracking_id=tracking_id)
    
    handler = DeleteOrderTrackingHandler(db)
    result = handler.handle(command)
    return result