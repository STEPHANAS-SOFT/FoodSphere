from fastapi import HTTPException, status
from dataclasses import dataclass
from sqlalchemy.orm import Session
from ..models import User, Vendor
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
