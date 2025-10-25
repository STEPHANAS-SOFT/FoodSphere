from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..shared import database
from ..shared.config import settings
from .. import schemas
from ..shared.api_key_route import verify_api_key
from ..services.commands import (
    CreateOrderCommand, CreateOrderHandler,
    UpdateOrderCommand, UpdateOrderHandler,
    DeleteOrderCommand, DeleteOrderHandler
)
from ..services.queries import (
    GetAllOrderQuery, GetAllOrderQueryHandler,
    GetOrderByIdQuery, GetOrderByIdQueryHandler,
    GetOrderByUserIdQuery, GetOrderByUserIdQueryHandler,
    GetOrderByVendorIdQuery, GetOrderByVendorIdQueryHandler,
    GetOrderByRiderIdQuery, GetOrderByRiderIdQueryHandler
)


# =================================================================================================================
#                                            ORDER ROUTES
# =================================================================================================================
order_router = APIRouter(
    prefix=f"{settings.api_prefix}/order", 
    tags=["Order"], 
    dependencies=[Depends(verify_api_key)]
)


# ==========================
# CREATE ORDER
# ==========================
@order_router.post("/", response_model=schemas.OrderResponse)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(database.get_db),
):
    command = CreateOrderCommand(
        user_id=order.user_id,
        vendor_id=order.vendor_id,
        delivery_address_id=order.delivery_address_id,
        subtotal=order.subtotal,
        total=order.total,
        rider_id=order.rider_id,
        status=order.status,
        delivery_fee=order.delivery_fee,
        notes=order.notes,
        estimated_delivery_time=order.estimated_delivery_time
    )
    handler = CreateOrderHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL ORDERS
# ==========================
@order_router.get("/", response_model=List[schemas.OrderResponse])
def get_all_orders(
    db: Session = Depends(database.get_db),
):
    query = GetAllOrderQuery()
    handler = GetAllOrderQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ORDER BY ID
# ==========================
@order_router.get("/{order_id}", response_model=schemas.OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetOrderByIdQuery(order_id=order_id)
    handler = GetOrderByIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ORDERS BY USER ID
# ==========================
@order_router.get("/user/{user_id}", response_model=List[schemas.OrderResponse])
def get_orders_by_user(
    user_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetOrderByUserIdQuery(user_id=user_id)
    handler = GetOrderByUserIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ORDERS BY VENDOR ID
# ==========================
@order_router.get("/vendor/{vendor_id}", response_model=List[schemas.OrderResponse])
def get_orders_by_vendor(
    vendor_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetOrderByVendorIdQuery(vendor_id=vendor_id)
    handler = GetOrderByVendorIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ORDERS BY RIDER ID
# ==========================
@order_router.get("/rider/{rider_id}", response_model=List[schemas.OrderResponse])
def get_orders_by_rider(
    rider_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetOrderByRiderIdQuery(rider_id=rider_id)
    handler = GetOrderByRiderIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# UPDATE ORDER BY ID
# ==========================
@order_router.put("/{order_id}", response_model=schemas.OrderResponse)
def update_order(
    order_id: int,
    order: schemas.OrderUpdate,
    db: Session = Depends(database.get_db),
):
    command = UpdateOrderCommand(
        order_id=order_id,
        rider_id=order.rider_id,
        status=order.status,
        delivery_fee=order.delivery_fee,
        total=order.total,
        notes=order.notes,
        estimated_delivery_time=order.estimated_delivery_time
    )
    handler = UpdateOrderHandler(db)
    return handler.handle(command)


# ==========================
# DELETE ORDER BY ID
# ==========================
@order_router.delete("/{order_id}")
def delete_order(
    order_id: int,
    db: Session = Depends(database.get_db),
):
    command = DeleteOrderCommand(order_id=order_id)
    handler = DeleteOrderHandler(db)
    return handler.handle(command)