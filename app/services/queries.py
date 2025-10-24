from fastapi import HTTPException, status
from dataclasses import dataclass
from sqlalchemy.orm import Session, joinedload
from ..models import User, Vendor, Item
from uuid import UUID


# ==============================================================================================================
#                                           USERS HANDLERS AND QUERIES
# ==============================================================================================================

# GET ALL USERS
@dataclass(frozen=True)
class GetAllUserQuery:
    pass


class GetAllUserQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllUserQuery, skip: int = 0, limit: int = 10):
        all_user = (self.db.query(User)
                    .offset(skip).limit(limit).all()
                   )
        if not all_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return all_user
    


# GET USER BY ID
@dataclass(frozen=True)
class GetUserByIdQuery:
    user_id: UUID


class GetUserByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetUserByIdQuery):
        user = self.db.query(User).filter(User.id == query.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with ID {0} not found".format(query.user_id))
        return user
    


# ==============================================================================================================
#                                           VENDOR HANDLERS AND QUERIES
# ==============================================================================================================

# GET ALL VENDORS
@dataclass(frozen=True)
class GetAllVendorQuery:
    pass


class GetAllVendorQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllVendorQuery, skip: int = 0, limit: int = 10):
        all_vendors = (self.db.query(Vendor)
                    .offset(skip).limit(limit).all()
                   )
        
        if not all_vendors:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
        return all_vendors


# GET VENDOR BY ID
@dataclass
class GetVendorByIdQuery:
    vendor_id: int

class GetVendorByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetVendorByIdQuery):

        vendor = (
                 self.db.query(Vendor)
                .options(joinedload(Vendor.items))
                .filter(Vendor.id == query.vendor_id)
                .first()
        )

        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor with ID {0} not found".format(query.vendor_id))
        return vendor
    


# ==========================
# GET VENDOR BY NAME
# ==========================
@dataclass(frozen=True)
class GetVendorByNameQuery:
    name: str


class GetVendorByNameQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetVendorByNameQuery):
        vendor_list = self.db.query(Vendor).filter(Vendor.name.ilike(f"%{query.name}%")).all()
        if not vendor_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor by name: {0} not found".format(query.name))
        return vendor_list




# ==============================================================================================================
#                                           ITEM HANDLERS AND QUERIES
# ==============================================================================================================
# ==========================
# GET ALL ITEMS
# ==========================
@dataclass(frozen=True)
class GetAllItemQuery:
    pass


class GetAllItemQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetAllItemQuery, skip: int = 0, limit: int = 10):
        all_items = (self.db.query(Item)
                    .offset(skip).limit(limit).all()
                   )
        if not all_items:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Items not found")
        return all_items


# ==========================
# GET ITEM BY ID
# ==========================
@dataclass
class GetItemByIdQuery:
    item_id: int

class GetItemByIdQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemByIdQuery):
        item = self.db.query(Item).filter(Item.id == query.item_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item with ID {0} not found".format(query.item_id))
        return item
    


# ==========================
# GET ITEM BY NAME
# ==========================
@dataclass(frozen=True)
class GetItemByNameQuery:
    name: str


class GetItemByNameQueryHandler:
    def __init__(self, db: Session):
        self.db = db

    def handle(self, query: GetItemByNameQuery):
        item_list = self.db.query(Item).filter(Item.name.ilike(f"%{query.name}%")).all()
        if not item_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item by name: {0} not found".format(query.name))
        return item_list