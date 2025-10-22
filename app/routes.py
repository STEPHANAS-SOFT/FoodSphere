from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .shared import database
from .shared.config import settings
from uuid import UUID
from . import schemas
from .shared.api_key_route import verify_api_key
# from .schemas import schemas
from .services.commands import (
    CreateUserCommand, CreateUserHandler,
    CreateVendorCommand, CreateVendorHandler
)
from .services.queries import (
    GetAllUserQuery, GetAllUserQueryHandler, GetAllVendorQuery,
    GetUserByIdQuery, GetUserByIdQueryHandler,
    GetAllVendorQuery, GetAllVendorQueryHandler,
)


# =================================================================================================================
#                                            USERS ROUTES
# =================================================================================================================
user_router = APIRouter(prefix=f"{settings.api_prefix}/user", tags=["User"], dependencies=[Depends(verify_api_key)])


# ==========================
# CREATE USERS
# ==========================
@user_router.post("/", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    command = CreateUserCommand(
        firebase_uid=user.firebase_uid,
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        fcm_token=user.fcm_token,
        latitude=user.latitude,
        longitude=user.longitude 
    )
    handler = CreateUserHandler(db)
    return handler.handle(command)




# ==========================
# GET ALL USERS
# ==========================
@user_router.get("/", response_model=List[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetAllUserQuery()
    handler = GetAllUserQueryHandler(db)
    return handler.handle(query)




# ==========================
# GET USER BY ID
# ==========================
@user_router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetUserByIdQuery(user_id=user_id)
    handler = GetUserByIdQueryHandler(db)
    return handler.handle(query)



# =================================================================================================================
#                                            VENDOR ROUTES
# =================================================================================================================
vendor_router = APIRouter(prefix=f"{settings.api_prefix}/vendor", tags=["Vendor"], dependencies=[Depends(verify_api_key)])

# ==========================
# CREATE VENDORS
# ==========================
@vendor_router.post("/", response_model=schemas.VendorResponse)
def create_vendor(
    vendor: schemas.VendorCreate,
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    command = CreateVendorCommand(
        firebase_uid=vendor.firebase_uid,
        name=vendor.name,
        vendor_type=vendor.vendor_type,
        email=vendor.email,
        phone_number=vendor.phone_number,
        address=vendor.address,
        latitude=vendor.latitude,
        longitude=vendor.longitude,
        description=vendor.description,
        logo_url=vendor.logo_url,
        has_own_delivery=vendor.has_own_delivery,
        is_active=vendor.is_active,
        fcm_token=vendor.fcm_token,
        opening_time=vendor.opening_time,
        closing_time=vendor.closing_time
    )
    handler = CreateVendorHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL VENDORS
# ==========================
@vendor_router.get("/", response_model=List[schemas.VendorResponse])
def get_all_vendors(
    db: Session = Depends(database.get_db),
    # current_user=Depends(oauth2.role_required(["admin"])),
):
    query = GetAllVendorQuery()
    handler = GetAllVendorQueryHandler(db)
    return handler.handle(query)
