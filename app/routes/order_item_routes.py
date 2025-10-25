from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..schemas import (
    OrderItemCreate,
    OrderItemUpdate,
    OrderItemResponse
)
from ..services.commands import (
    CreateOrderItemCommand,
    CreateOrderItemHandler,
    UpdateOrderItemCommand,
    UpdateOrderItemHandler,
    DeleteOrderItemCommand,
    DeleteOrderItemHandler
)
from ..services.queries import (
    GetOrderItemsQuery,
    GetOrderItemQuery
)

router = APIRouter(
    prefix="/order-items",
    tags=["order-items"]
)


@router.post("/", response_model=OrderItemResponse)
async def create_order_item(
    order_item: OrderItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Create a new order item"""
    command = CreateOrderItemCommand(
        order_id=order_item.order_id,
        item_id=order_item.item_id,
        variation_id=order_item.variation_id,
        quantity=order_item.quantity,
        unit_price=order_item.unit_price,
        subtotal=order_item.subtotal,
        notes=order_item.notes
    )
    
    handler = CreateOrderItemHandler(db)
    new_order_item = handler.handle(command)
    return new_order_item


@router.get("/", response_model=List[OrderItemResponse])
async def get_order_items(
    order_id: Optional[int] = Query(None, description="Filter by order ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get order items with optional filtering"""
    query_handler = GetOrderItemsQuery(db)
    order_items = query_handler.handle(order_id=order_id, skip=skip, limit=limit)
    return order_items


@router.get("/{order_item_id}", response_model=OrderItemResponse)
async def get_order_item(
    order_item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get a specific order item by ID"""
    query_handler = GetOrderItemQuery(db)
    order_item = query_handler.handle(order_item_id)
    return order_item


@router.put("/{order_item_id}", response_model=OrderItemResponse)
async def update_order_item(
    order_item_id: int,
    order_item_update: OrderItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Update an existing order item"""
    command = UpdateOrderItemCommand(
        order_item_id=order_item_id,
        quantity=order_item_update.quantity,
        unit_price=order_item_update.unit_price,
        subtotal=order_item_update.subtotal,
        notes=order_item_update.notes
    )
    
    handler = UpdateOrderItemHandler(db)
    updated_order_item = handler.handle(command)
    return updated_order_item


@router.delete("/{order_item_id}")
async def delete_order_item(
    order_item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Delete an order item"""
    command = DeleteOrderItemCommand(order_item_id=order_item_id)
    
    handler = DeleteOrderItemHandler(db)
    result = handler.handle(command)
    return result