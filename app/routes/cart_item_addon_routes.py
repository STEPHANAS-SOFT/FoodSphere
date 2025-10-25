from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..schemas import (
    CartItemAddonCreate,
    CartItemAddonResponse
)
from ..services.commands import (
    CreateCartItemAddonCommand,
    CreateCartItemAddonHandler,
    DeleteCartItemAddonCommand,
    DeleteCartItemAddonHandler
)
from ..services.queries import (
    GetCartItemAddonsQuery,
    GetCartItemAddonQuery
)

router = APIRouter(
    prefix="/cart-item-addons",
    tags=["cart-item-addons"]
)


@router.post("/", response_model=CartItemAddonResponse)
async def create_cart_item_addon(
    addon: CartItemAddonCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Create a new cart item addon"""
    command = CreateCartItemAddonCommand(
        cart_item_id=addon.cart_item_id,
        addon_id=addon.addon_id,
        price=addon.price
    )
    
    handler = CreateCartItemAddonHandler(db)
    new_addon = handler.handle(command)
    return new_addon


@router.get("/", response_model=List[CartItemAddonResponse])
async def get_cart_item_addons(
    cart_item_id: Optional[int] = Query(None, description="Filter by cart item ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get cart item addons with optional filtering"""
    query_handler = GetCartItemAddonsQuery(db)
    addons = query_handler.handle(cart_item_id=cart_item_id, skip=skip, limit=limit)
    return addons


@router.get("/{addon_id}", response_model=CartItemAddonResponse)
async def get_cart_item_addon(
    addon_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get a specific cart item addon by ID"""
    query_handler = GetCartItemAddonQuery(db)
    addon = query_handler.handle(addon_id)
    return addon


@router.delete("/{addon_id}")
async def delete_cart_item_addon(
    addon_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Delete a cart item addon"""
    command = DeleteCartItemAddonCommand(cart_item_addon_id=addon_id)
    
    handler = DeleteCartItemAddonHandler(db)
    result = handler.handle(command)
    return result