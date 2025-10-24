from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from enum import Enum


# ====================================================
# USER SCHEMAS
# ====================================================

class UserBase(BaseModel):
    firebase_uid: str = Field(..., description="Firebase authentication UID")
    email: EmailStr
    phone_number: str 
    full_name: str 
    fcm_token: Optional[str] 
    latitude: Optional[float] 
    longitude: Optional[float] 


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    fcm_token: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None



class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ====================================================
# ITEM SCHEMAS
# ====================================================

class ItemBase(BaseModel):
    name: str
    base_price: float
    description: Optional[str]
    image_url: Optional[HttpUrl]
    is_available: Optional[bool]
    allows_addons: Optional[bool]
    vendor_id: int
    # category_id: int


    class Config:
        orm_mode = True

class ItemCreate(ItemBase):
    pass

    class Config:
        orm_mode = True

class ItemUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    base_price: Optional[float]
    image_url: Optional[HttpUrl]
    is_available: Optional[bool]
    allows_addons: Optional[bool]
    # category_id: Optional[int]

    class Config:
        orm_mode = True

class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True



# ====================================================
# VENDOR SCHEMAS
# ====================================================
class VendorType(str, Enum):
    RESTAURANT = "restaurant"
    SUPERMARKET = "supermarket"
    PHARMACY = "pharmacy"



class VendorBase(BaseModel):
    firebase_uid: str
    name: str
    vendor_type: VendorType
    description: Optional[str] = None
    email: EmailStr
    phone_number: str
    address: str
    latitude: float
    longitude: float
    logo_url: Optional[str] = None
    has_own_delivery: Optional[bool] = False
    is_active: Optional[bool] = True
    fcm_token: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None



class VendorCreate(VendorBase):
    pass



class VendorUpdate(BaseModel):
    name: Optional[str] = None
    vendor_type: Optional[VendorType] = None
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    logo_url: Optional[str] = None
    has_own_delivery: Optional[bool] = None
    is_active: Optional[bool] = None
    fcm_token: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None



class VendorResponse(VendorBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: Optional[List[ItemResponse]]

    class Config:
        orm_mode = True



