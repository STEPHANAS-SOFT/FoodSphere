from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..schemas import (
    OrderItemAddonCreate,
    OrderItemAddonResponse
)
from ..services.commands import (
    CreateOrderItemAddonCommand,
    CreateOrderItemAddonHandler,
    DeleteOrderItemAddonCommand,
    DeleteOrderItemAddonHandler
)
from ..services.queries import (
    GetOrderItemAddonsQuery,
    GetOrderItemAddonQuery
)

router = APIRouter(
    prefix="/order-item-addons",
    tags=["order-item-addons"]
)


@router.post("/", response_model=OrderItemAddonResponse)
async def create_order_item_addon(
    addon: OrderItemAddonCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Create a new order item addon"""
    command = CreateOrderItemAddonCommand(
        order_item_id=addon.order_item_id,
        addon_id=addon.addon_id,
        price=addon.price
    )
    
    handler = CreateOrderItemAddonHandler(db)
    new_addon = handler.handle(command)
    return new_addon


@router.get("/", response_model=List[OrderItemAddonResponse])
async def get_order_item_addons(
    order_item_id: Optional[int] = Query(None, description="Filter by order item ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get order item addons with optional filtering"""
    query_handler = GetOrderItemAddonsQuery(db)
    addons = query_handler.handle(order_item_id=order_item_id, skip=skip, limit=limit)
    return addons


@router.get("/{addon_id}", response_model=OrderItemAddonResponse)
async def get_order_item_addon(
    addon_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get a specific order item addon by ID"""
    query_handler = GetOrderItemAddonQuery(db)
    addon = query_handler.handle(addon_id)
    return addon


@router.delete("/{addon_id}")
async def delete_order_item_addon(
    addon_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Delete an order item addon"""
    command = DeleteOrderItemAddonCommand(order_item_addon_id=addon_id)
    
    handler = DeleteOrderItemAddonHandler(db)
    result = handler.handle(command)
    return result