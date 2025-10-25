from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..shared import database
from ..shared.config import settings
from .. import schemas
from ..shared.api_key_route import verify_api_key
from ..services.commands import (
    CreateRiderCommand, CreateRiderHandler,
    UpdateRiderCommand, UpdateRiderHandler,
    DeleteRiderCommand, DeleteRiderHandler
)
from ..services.queries import (
    GetAllRiderQuery, GetAllRiderQueryHandler,
    GetRiderByIdQuery, GetRiderByIdQueryHandler,
    GetRiderByNameQuery, GetRiderByNameQueryHandler
)


# =================================================================================================================
#                                            RIDER ROUTES
# =================================================================================================================
rider_router = APIRouter(
    prefix=f"{settings.api_prefix}/rider", 
    tags=["Rider"], 
    dependencies=[Depends(verify_api_key)]
)


# ==========================
# CREATE RIDER
# ==========================
@rider_router.post("/", response_model=schemas.RiderResponse)
def create_rider(
    rider: schemas.RiderCreate,
    db: Session = Depends(database.get_db),
):
    command = CreateRiderCommand(
        firebase_uid=rider.firebase_uid,
        full_name=rider.full_name,
        email=rider.email,
        phone_number=rider.phone_number,
        vehicle_type=rider.vehicle_type,
        vehicle_number=rider.vehicle_number,
        license_number=rider.license_number,
        is_verified=rider.is_verified,
        is_active=rider.is_active,
        current_latitude=rider.current_latitude,
        current_longitude=rider.current_longitude,
        fcm_token=rider.fcm_token,
        status=rider.status
    )
    handler = CreateRiderHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL RIDERS
# ==========================
@rider_router.get("/", response_model=List[schemas.RiderResponse])
def get_all_riders(
    db: Session = Depends(database.get_db),
):
    query = GetAllRiderQuery()
    handler = GetAllRiderQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET RIDER BY ID
# ==========================
@rider_router.get("/{rider_id}", response_model=schemas.RiderResponse)
def get_rider(
    rider_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetRiderByIdQuery(rider_id=rider_id)
    handler = GetRiderByIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET RIDER BY NAME
# ==========================
@rider_router.get("/name/{name}", response_model=List[schemas.RiderResponse])
def get_rider_by_name(
    name: str,
    db: Session = Depends(database.get_db),
):
    query = GetRiderByNameQuery(name=name)
    handler = GetRiderByNameQueryHandler(db)
    return handler.handle(query)


# ==========================
# UPDATE RIDER BY ID
# ==========================
@rider_router.put("/{rider_id}", response_model=schemas.RiderResponse)
def update_rider(
    rider_id: int,
    rider: schemas.RiderUpdate,
    db: Session = Depends(database.get_db),
):
    command = UpdateRiderCommand(
        rider_id=rider_id,
        full_name=rider.full_name,
        email=rider.email,
        phone_number=rider.phone_number,
        vehicle_type=rider.vehicle_type,
        vehicle_number=rider.vehicle_number,
        license_number=rider.license_number,
        is_verified=rider.is_verified,
        is_active=rider.is_active,
        current_latitude=rider.current_latitude,
        current_longitude=rider.current_longitude,
        fcm_token=rider.fcm_token,
        status=rider.status
    )
    handler = UpdateRiderHandler(db)
    return handler.handle(command)


# ==========================
# DELETE RIDER BY ID
# ==========================
@rider_router.delete("/{rider_id}")
def delete_rider(
    rider_id: int,
    db: Session = Depends(database.get_db),
):
    command = DeleteRiderCommand(rider_id=rider_id)
    handler = DeleteRiderHandler(db)
    return handler.handle(command)