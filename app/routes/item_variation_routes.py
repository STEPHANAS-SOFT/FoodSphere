from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..shared import database
from ..shared.config import settings
from .. import schemas
from ..shared.api_key_route import verify_api_key
from ..services.commands import (
    CreateItemVariationCommand, CreateItemVariationHandler,
    UpdateItemVariationCommand, UpdateItemVariationHandler,
    DeleteItemVariationCommand, DeleteItemVariationHandler
)
from ..services.queries import (
    GetAllItemVariationQuery, GetAllItemVariationQueryHandler,
    GetItemVariationByIdQuery, GetItemVariationByIdQueryHandler,
    GetItemVariationByItemIdQuery, GetItemVariationByItemIdQueryHandler
)


# =================================================================================================================
#                                            ITEM VARIATION ROUTES
# =================================================================================================================
item_variation_router = APIRouter(
    prefix=f"{settings.api_prefix}/item-variation", 
    tags=["Item Variation"], 
    dependencies=[Depends(verify_api_key)]
)


# ==========================
# CREATE ITEM VARIATION
# ==========================
@item_variation_router.post("/", response_model=schemas.ItemVariationResponse)
def create_item_variation(
    variation: schemas.ItemVariationCreate,
    db: Session = Depends(database.get_db),
):
    command = CreateItemVariationCommand(
        item_id=variation.item_id,
        name=variation.name,
        description=variation.description,
        price=variation.price,
        is_available=variation.is_available
    )
    handler = CreateItemVariationHandler(db)
    return handler.handle(command)


# ==========================
# GET ALL ITEM VARIATIONS
# ==========================
@item_variation_router.get("/", response_model=List[schemas.ItemVariationResponse])
def get_all_item_variations(
    db: Session = Depends(database.get_db),
):
    query = GetAllItemVariationQuery()
    handler = GetAllItemVariationQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ITEM VARIATION BY ID
# ==========================
@item_variation_router.get("/{variation_id}", response_model=schemas.ItemVariationResponse)
def get_item_variation(
    variation_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetItemVariationByIdQuery(variation_id=variation_id)
    handler = GetItemVariationByIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# GET ITEM VARIATIONS BY ITEM ID
# ==========================
@item_variation_router.get("/item/{item_id}", response_model=List[schemas.ItemVariationResponse])
def get_item_variations_by_item(
    item_id: int,
    db: Session = Depends(database.get_db),
):
    query = GetItemVariationByItemIdQuery(item_id=item_id)
    handler = GetItemVariationByItemIdQueryHandler(db)
    return handler.handle(query)


# ==========================
# UPDATE ITEM VARIATION BY ID
# ==========================
@item_variation_router.put("/{variation_id}", response_model=schemas.ItemVariationResponse)
def update_item_variation(
    variation_id: int,
    variation: schemas.ItemVariationUpdate,
    db: Session = Depends(database.get_db),
):
    command = UpdateItemVariationCommand(
        variation_id=variation_id,
        name=variation.name,
        description=variation.description,
        price=variation.price,
        is_available=variation.is_available
    )
    handler = UpdateItemVariationHandler(db)
    return handler.handle(command)


# ==========================
# DELETE ITEM VARIATION BY ID
# ==========================
@item_variation_router.delete("/{variation_id}")
def delete_item_variation(
    variation_id: int,
    db: Session = Depends(database.get_db),
):
    command = DeleteItemVariationCommand(variation_id=variation_id)
    handler = DeleteItemVariationHandler(db)
    return handler.handle(command)