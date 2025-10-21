from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr
from sqlalchemy.orm import Session
from ..models import User, Vendor, VendorType
from dataclasses import dataclass
from typing import Optional


# ====================================================================================================
# CREATE USERS
# ====================================================================================================
@dataclass
class CreateUserCommand:
    firebase_uid: str
    email: EmailStr
    phone_number: str 
    full_name: str 
    fcm_token: Optional[str] 
    latitude: Optional[float] 
    longitude: Optional[float] 


class CreateUserHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: CreateUserCommand):

        # create user
        user = User(
            firebase_uid=command.firebase_uid,
            email=command.email,
            phone_number=command.phone_number,
            full_name=command.full_name,
            fcm_token=command.fcm_token,
            latitude=command.latitude,  
            longitude=command.longitude,
        )
        self.db.add(user)
        self.db.commit() 
        self.db.refresh(user)
        return user
    



# ====================================================================================================
# CREATE VENDORS
# ====================================================================================================
@dataclass
class CreateVendorCommand:
    firebase_uid: str
    name: str
    vendor_type: VendorType  
    email: EmailStr
    phone_number: str
    address: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    logo_url: Optional[str] = None
    has_own_delivery: Optional[bool] = False
    is_active: Optional[bool] = True
    fcm_token: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None

class CreateVendorHandler:
        def __init__(self, db: Session):
            self.db = db

        def handle(self, command: CreateVendorCommand):

            # Ensure vendor_type is Enum instance
            if isinstance(command.vendor_type, str):
                try:
                    command.vendor_type = VendorType(command.vendor_type.lower())
                except ValueError:
                    raise ValueError(
                        f"Invalid vendor type: '{command.vendor_type}'. "
                        f"Must be one of: {[v.value for v in VendorType]}"
                    )
                
            # create vendor
            vendor = Vendor(
                firebase_uid=command.firebase_uid,
                name=command.name,
                vendor_type=command.vendor_type,
                description=command.description,
                email=command.email,
                phone_number=command.phone_number,
                address=command.address,
                latitude=command.latitude,
                longitude=command.longitude,
                logo_url=command.logo_url,
                has_own_delivery=command.has_own_delivery,
                is_active=command.is_active,
                fcm_token=command.fcm_token,
                opening_time=command.opening_time,
                closing_time=command.closing_time,
            )
            self.db.add(vendor)
            self.db.commit() 
            self.db.refresh(vendor)
            return vendor