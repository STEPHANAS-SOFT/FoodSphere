from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..shared import database
from ..shared.config import settings
from .. import schemas
from ..shared.api_key_route import verify_api_key
from ..services.commands import (
    CreateCartCommand, CreateCartHandler,
    UpdateCartCommand, UpdateCartHandler,
    DeleteCartCommand, DeleteCartHandler
)
from ..services.queries import (
    GetAllCartQuery, GetAllCartQueryHandler,
    GetCartByIdQuery, GetCartByIdQueryHandler,
    GetCartByUserIdQuery, GetCartByUserIdQueryHandler
)


# =================================================================================================================
#                                            CART ROUTES
# =================================================================================================================
cart_router = APIRouter(
    prefix=f"{settings.api_prefix}/cart", 
    tags=["Cart"], 
    dependencies=[Depends(verify_api_key)]
)


# ==========================
# CREATE CART
# ==========================
@cart_router.post("/", response_model=schemas.CartResponse)
def create_cart(
    cart: schemas.CartCreate,
    db: Session = Depends(database.get_db),
):
    command = CreateCartCommand(
        user_id=cart.user_id,
        vendor_id=cart.vendor_id,
        subtotal=cart.subtotal,
        notes=cart.notes,
        expires_at=cart.expires_at
    )
    handler = CreateCartHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL CARTS
# ==========================
@cart_router.get("/", response_model=List[schemas.CartResponse])
def get_all_carts(
    db: Session = Depends(database.get_db),
):
    query = GetAllCartQuery()
    handler = GetAllCartQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET CART BY ID
# ==========================
@cart_router.get("/{cart_id}", response_model=schemas.CartResponse)
def get_cart(
    cart_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetCartByIdQuery(cart_id=cart_id)
    handler = GetCartByIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET CARTS BY USER ID
# ==========================
@cart_router.get("/user/{user_id}", response_model=List[schemas.CartResponse])
def get_carts_by_user(
    user_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetCartByUserIdQuery(user_id=user_id)
    handler = GetCartByUserIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# UPDATE CART BY ID
# ==========================
@cart_router.put("/{cart_id}", response_model=schemas.CartResponse)
def update_cart(
    cart_id: int,
    cart: schemas.CartUpdate,
    db: Session = Depends(database.get_db),
):
    command = UpdateCartCommand(
        cart_id=cart_id,
        subtotal=cart.subtotal,
        notes=cart.notes,
        expires_at=cart.expires_at
    )
    handler = UpdateCartHandler(db)
    return handler.handle(command)


# ==========================
# DELETE CART BY ID
# ==========================
@cart_router.delete("/{cart_id}")
def delete_cart(
    cart_id: int,
    db: Session = Depends(database.get_db),
):
    command = DeleteCartCommand(cart_id=cart_id)
    handler = DeleteCartHandler(db)
    return handler.handle(command)