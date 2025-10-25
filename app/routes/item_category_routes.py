from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..shared import database
from ..shared.config import settings
from .. import schemas
from ..shared.api_key_route import verify_api_key
from ..services.commands import (
    CreateItemCategoryCommand, CreateItemCategoryHandler,
    UpdateItemCategoryCommand, UpdateItemCategoryHandler,
    DeleteItemCategoryCommand, DeleteItemCategoryHandler
)
from ..services.queries import (
    GetAllItemCategoryQuery, GetAllItemCategoryQueryHandler,
    GetItemCategoryByIdQuery, GetItemCategoryByIdQueryHandler,
    GetItemCategoryByNameQuery, GetItemCategoryByNameQueryHandler
)


# =================================================================================================================
#                                            ITEM CATEGORY ROUTES
# =================================================================================================================
item_category_router = APIRouter(
    prefix=f"{settings.api_prefix}/item-category", 
    tags=["Item Category"], 
    dependencies=[Depends(verify_api_key)]
)


# ==========================
# CREATE ITEM CATEGORY
# ==========================
@item_category_router.post("/", response_model=schemas.ItemCategoryResponse)
def create_item_category(
    category: schemas.ItemCategoryCreate,
    db: Session = Depends(database.get_db),
):
    command = CreateItemCategoryCommand(
        name=category.name,
        description=category.description
    )
    handler = CreateItemCategoryHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL ITEM CATEGORIES
# ==========================
@item_category_router.get("/", response_model=List[schemas.ItemCategoryResponse])
def get_all_item_categories(
    db: Session = Depends(database.get_db),
):
    query = GetAllItemCategoryQuery()
    handler = GetAllItemCategoryQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ITEM CATEGORY BY ID
# ==========================
@item_category_router.get("/{category_id}", response_model=schemas.ItemCategoryResponse)
def get_item_category(
    category_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetItemCategoryByIdQuery(category_id=category_id)
    handler = GetItemCategoryByIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ITEM CATEGORY BY NAME
# ==========================
@item_category_router.get("/name/{name}", response_model=List[schemas.ItemCategoryResponse])
def get_item_category_by_name(
    name: str,
    db: Session = Depends(database.get_db),
):
    query = GetItemCategoryByNameQuery(name=name)
    handler = GetItemCategoryByNameQueryHandler(db)
    return handler.handle(query)


# ==========================
# UPDATE ITEM CATEGORY BY ID
# ==========================
@item_category_router.put("/{category_id}", response_model=schemas.ItemCategoryResponse)
def update_item_category(
    category_id: int,
    category: schemas.ItemCategoryUpdate,
    db: Session = Depends(database.get_db),
):
    command = UpdateItemCategoryCommand(
        category_id=category_id,
        name=category.name,
        description=category.description
    )
    handler = UpdateItemCategoryHandler(db)
    return handler.handle(command)


# ==========================
# DELETE ITEM CATEGORY BY ID
# ==========================
@item_category_router.delete("/{category_id}")
def delete_item_category(
    category_id: int,
    db: Session = Depends(database.get_db),
):
    command = DeleteItemCategoryCommand(category_id=category_id)
    handler = DeleteItemCategoryHandler(db)
    return handler.handle(command)