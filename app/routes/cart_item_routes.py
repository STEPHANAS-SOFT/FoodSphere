from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..schemas import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse
)
from ..services.commands import (
    CreateCartItemCommand,
    CreateCartItemHandler,
    UpdateCartItemCommand,
    UpdateCartItemHandler,
    DeleteCartItemCommand,
    DeleteCartItemHandler
)
from ..services.queries import (
    GetCartItemsQuery,
    GetCartItemQuery
)

router = APIRouter(
    prefix="/cart-items",
    tags=["cart-items"]
)


@router.post("/", response_model=CartItemResponse)
async def create_cart_item(
    cart_item: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Create a new cart item"""
    command = CreateCartItemCommand(
        cart_id=cart_item.cart_id,
        item_id=cart_item.item_id,
        variation_id=cart_item.variation_id,
        quantity=cart_item.quantity,
        unit_price=cart_item.unit_price,
        subtotal=cart_item.subtotal,
        notes=cart_item.notes
    )
    
    handler = CreateCartItemHandler(db)
    new_cart_item = handler.handle(command)
    return new_cart_item


@router.get("/", response_model=List[CartItemResponse])
async def get_cart_items(
    cart_id: Optional[int] = Query(None, description="Filter by cart ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get cart items with optional filtering"""
    query_handler = GetCartItemsQuery(db)
    cart_items = query_handler.handle(cart_id=cart_id, skip=skip, limit=limit)
    return cart_items


@router.get("/{cart_item_id}", response_model=CartItemResponse)
async def get_cart_item(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get a specific cart item by ID"""
    query_handler = GetCartItemQuery(db)
    cart_item = query_handler.handle(cart_item_id)
    return cart_item


@router.put("/{cart_item_id}", response_model=CartItemResponse)
async def update_cart_item(
    cart_item_id: int,
    cart_item_update: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Update an existing cart item"""
    command = UpdateCartItemCommand(
        cart_item_id=cart_item_id,
        quantity=cart_item_update.quantity,
        unit_price=cart_item_update.unit_price,
        subtotal=cart_item_update.subtotal,
        notes=cart_item_update.notes
    )
    
    handler = UpdateCartItemHandler(db)
    updated_cart_item = handler.handle(command)
    return updated_cart_item


@router.delete("/{cart_item_id}")
async def delete_cart_item(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Delete a cart item"""
    command = DeleteCartItemCommand(cart_item_id=cart_item_id)
    
    handler = DeleteCartItemHandler(db)
    result = handler.handle(command)
    return result