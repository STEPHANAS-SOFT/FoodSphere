from fastapi import HTTPException, status
from datetime import datetime
from pydantic import EmailStr, HttpUrl
from sqlalchemy.orm import Session
from ..models import User, Vendor, VendorType, Item
from dataclasses import dataclass
from typing import Optional, List


# =============================================================================================================
# USER COMMANDS
# =============================================================================================================

# ==================
# CREATE USERS
# ==================
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
    


# ==========================
# UPDATE USER BY ID
# ==========================
@dataclass(frozen=True)
class UpdateUserCommand:
    user_id: int
    firebase_uid: str
    email: EmailStr
    phone_number: str 
    full_name: str 
    fcm_token: Optional[str] 
    latitude: Optional[float] 
    longitude: Optional[float] 

class UpdateUserHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateUserCommand):
        user_query = self.db.query(User).filter(User.id == command.user_id)
        user = user_query.first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID: {command.user_id} not found")

        user_query.update({
            User.firebase_uid: command.firebase_uid,
            User.email: command.email,
            User.phone_number: command.phone_number,
            User.full_name: command.full_name,
            User.fcm_token: command.fcm_token,
            User.latitude: command.latitude,
            User.longitude: command.longitude,
        })
        
        self.db.commit()
        return user_query.first()





# =======================
# DELETE USER BY ID
# =======================
@dataclass(frozen=True)
class DeleteUserCommand:
    user_id: int

class DeleteUserHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DeleteUserCommand):
        user = self.db.query(User).filter(User.id == command.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with ID: {command.user_id} not found")

        self.db.delete(user)
        self.db.commit()
        return {"msg": f"User with id: {command.user_id} deleted successfully"}


# =============================================================================================================
# VENDOR COMMANDS
# =============================================================================================================

# ======================
# CREATE VENDORS
# ======================
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
    items: Optional[List[dict]] = None 

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
        




# ==========================
# UPDATE VENDOR BY ID
# ==========================
@dataclass(frozen=True)
class UpdateVendorCommand:
    vendor_id: int
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

class UpdateVendorHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateVendorCommand):
        vendor_query = self.db.query(Vendor).filter(Vendor.id == command.vendor_id)
        vendor = vendor_query.first()
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vendor with ID: {command.vendor_id} not found")

        vendor_query.update({
            Vendor.name: command.name,
            Vendor.vendor_type: command.vendor_type,
            Vendor.email: command.email,
            Vendor.phone_number: command.phone_number,
            Vendor.address: command.address,
            Vendor.latitude: command.latitude,
            Vendor.longitude: command.longitude,
            Vendor.description: command.description,
            Vendor.logo_url: command.logo_url,
            Vendor.has_own_delivery: command.has_own_delivery,
            Vendor.is_active: command.is_active,
            Vendor.fcm_token: command.fcm_token,
            Vendor.opening_time: command.opening_time,
            Vendor.closing_time: command.closing_time,
        })
        self.db.commit()
        return vendor_query.first()
    




# =======================
# DELETE VENDOR BY ID
# =======================
@dataclass(frozen=True)
class DeleteVendorCommand:
    vendor_id: int

class DeleteVendorHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DeleteVendorCommand):
        vendor = self.db.query(Vendor).filter(Vendor.id == command.vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vendor with ID: {command.vendor_id} not found")

        self.db.delete(vendor)
        self.db.commit()
        return {"msg": f"Vendor with id: {command.vendor_id} deleted successfully"}
    






# =============================================================================================================
# ITEM COMMANDS
# =============================================================================================================

# ======================
# CREATE ITEMS
# ======================
@dataclass
class CreateItemCommand:
    name: str
    base_price: float
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    is_available: Optional[bool] = True
    allows_addons: Optional[bool] = False
    # category_id: int
    # vendor_id: int


class CreateItemHandler:
        def __init__(self, db: Session):
            self.db = db

        def handle(self, command: CreateItemCommand):

            # create item
            item = Item(
                name=command.name,
                base_price=command.base_price,
                description=command.description,
                image_url=command.image_url,
                is_available=command.is_available,
                allows_addons=command.allows_addons,
                # category_id=command.category_id,
                # vendor_id=command.vendor_id,
            )

            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item





# ==========================
# UPDATE ITEM BY ID
# ==========================
@dataclass(frozen=True)
class UpdateItemCommand:
    item_id: int
    name: str
    base_price: float
    description: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    is_available: Optional[bool] = True
    allows_addons: Optional[bool] = False


class UpdateItemHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, command: UpdateItemCommand):
        item_query = self.db.query(Item).filter(Item.id == command.item_id)
        item = item_query.first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with ID: {command.item_id} not found")

        item_query.update({
            Item.name: command.name,
            Item.description: command.description,
            Item.base_price: command.base_price,
            Item.image_url: command.image_url,
            Item.is_available: command.is_available,
            Item.allows_addons: command.allows_addons,
        })
        self.db.commit()
        return item_query.first()





# =======================
# DELETE ITEM BY ID
# =======================
@dataclass(frozen=True)
class DeleteItemCommand:
    item_id: int

class DeleteItemHandler:
    def __init__(self, db):
        self.db = db

    def handle(self, command: DeleteItemCommand):
        item = self.db.query(Item).filter(Item.id == command.item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with ID: {command.item_id} not found")

        self.db.delete(item)
        self.db.commit()
        return {"msg": f"Item with id: {command.item_id} deleted successfully"}