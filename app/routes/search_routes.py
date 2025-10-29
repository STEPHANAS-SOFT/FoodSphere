from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from math import radians, cos, sin, asin, sqrt

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..schemas import VendorResponse, ItemResponse
from ..models import Vendor, Item, ItemCategory, VendorType
from ..services.queries import GetAllVendorQueryHandler, GetAllVendorQuery


router = APIRouter(
    prefix="/search",
    tags=["search"]
)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


@router.get("/vendors", response_model=List[VendorResponse])
async def search_vendors(
    query: str = Query(..., description="Search term for vendor name or description"),
    vendor_type: Optional[VendorType] = Query(None, description="Filter by vendor type"),
    latitude: Optional[float] = Query(None, description="User latitude for distance calculation"),
    longitude: Optional[float] = Query(None, description="User longitude for distance calculation"),
    max_distance: Optional[float] = Query(None, description="Maximum distance in kilometers"),
    is_active: Optional[bool] = Query(True, description="Filter active vendors only"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Search vendors by name, description, type, and location"""
    
    # Base query
    vendors_query = db.query(Vendor)
    
    # Apply filters
    if query:
        search_term = f"%{query.lower()}%"
        vendors_query = vendors_query.filter(
            (Vendor.name.ilike(search_term)) | 
            (Vendor.description.ilike(search_term))
        )
    
    if vendor_type:
        vendors_query = vendors_query.filter(Vendor.vendor_type == vendor_type)
    
    if is_active is not None:
        vendors_query = vendors_query.filter(Vendor.is_active == is_active)
    
    # Get vendors
    vendors = vendors_query.offset(skip).limit(limit).all()
    
    # Filter by distance if location provided
    if latitude is not None and longitude is not None and max_distance is not None:
        filtered_vendors = []
        for vendor in vendors:
            if vendor.latitude and vendor.longitude:
                distance = haversine_distance(latitude, longitude, vendor.latitude, vendor.longitude)
                if distance <= max_distance:
                    # Add distance to vendor object for client use
                    vendor.distance = distance
                    filtered_vendors.append(vendor)
        vendors = filtered_vendors
    
    return vendors


@router.get("/items", response_model=List[ItemResponse])
async def search_menu_items(
    query: str = Query(..., description="Search term for item name or description"),
    vendor_id: Optional[int] = Query(None, description="Filter items by specific vendor"),
    category_id: Optional[int] = Query(None, description="Filter items by category"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    is_available: Optional[bool] = Query(True, description="Filter available items only"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Search menu items by name, description, vendor, category, and price range"""
    
    # Base query with vendor join for active vendor filtering
    items_query = db.query(Item).join(Vendor, Item.vendor_id == Vendor.id)
    
    # Apply filters
    if query:
        search_term = f"%{query.lower()}%"
        items_query = items_query.filter(
            (Item.name.ilike(search_term)) | 
            (Item.description.ilike(search_term))
        )
    
    if vendor_id:
        items_query = items_query.filter(Item.vendor_id == vendor_id)
    
    if category_id:
        items_query = items_query.filter(Item.category_id == category_id)
    
    if min_price is not None:
        items_query = items_query.filter(Item.price >= min_price)
    
    if max_price is not None:
        items_query = items_query.filter(Item.price <= max_price)
    
    if is_available is not None:
        items_query = items_query.filter(Item.is_available == is_available)
    
    # Only show items from active vendors
    items_query = items_query.filter(Vendor.is_active == True)
    
    items = items_query.offset(skip).limit(limit).all()
    return items


@router.get("/vendors/nearby", response_model=List[VendorResponse])
async def get_nearby_vendors(
    latitude: float = Query(..., description="User latitude"),
    longitude: float = Query(..., description="User longitude"),
    radius: float = Query(10.0, ge=0.1, le=50.0, description="Search radius in kilometers"),
    vendor_type: Optional[VendorType] = Query(None, description="Filter by vendor type"),
    is_active: bool = Query(True, description="Filter active vendors only"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get nearby vendors within specified radius, sorted by distance"""
    
    # Base query
    vendors_query = db.query(Vendor)
    
    # Apply filters
    if vendor_type:
        vendors_query = vendors_query.filter(Vendor.vendor_type == vendor_type)
    
    if is_active:
        vendors_query = vendors_query.filter(Vendor.is_active == is_active)
    
    # Get all vendors (we'll filter by distance)
    all_vendors = vendors_query.all()
    
    # Calculate distances and filter
    nearby_vendors = []
    for vendor in all_vendors:
        if vendor.latitude and vendor.longitude:
            distance = haversine_distance(latitude, longitude, vendor.latitude, vendor.longitude)
            if distance <= radius:
                vendor.distance = distance
                nearby_vendors.append(vendor)
    
    # Sort by distance
    nearby_vendors.sort(key=lambda v: v.distance)
    
    # Apply pagination
    start = skip
    end = skip + limit
    paginated_vendors = nearby_vendors[start:end]
    
    return paginated_vendors


@router.get("/vendors/by-category/{category_id}", response_model=List[VendorResponse])
async def get_vendors_by_category(
    category_id: int,
    latitude: Optional[float] = Query(None, description="User latitude for distance calculation"),
    longitude: Optional[float] = Query(None, description="User longitude for distance calculation"),
    max_distance: Optional[float] = Query(None, description="Maximum distance in kilometers"),
    is_active: bool = Query(True, description="Filter active vendors only"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get vendors that have items in a specific category"""
    
    # Verify category exists
    category = db.query(ItemCategory).filter(ItemCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Get vendors that have items in this category
    vendors_query = db.query(Vendor).join(Item, Vendor.id == Item.vendor_id).filter(
        Item.category_id == category_id
    ).distinct()
    
    if is_active:
        vendors_query = vendors_query.filter(Vendor.is_active == is_active)
    
    vendors = vendors_query.offset(skip).limit(limit).all()
    
    # Filter by distance if location provided
    if latitude is not None and longitude is not None and max_distance is not None:
        filtered_vendors = []
        for vendor in vendors:
            if vendor.latitude and vendor.longitude:
                distance = haversine_distance(latitude, longitude, vendor.latitude, vendor.longitude)
                if distance <= max_distance:
                    vendor.distance = distance
                    filtered_vendors.append(vendor)
        vendors = filtered_vendors
    
    return vendors


@router.get("/trending/vendors", response_model=List[VendorResponse])
async def get_trending_vendors(
    vendor_type: Optional[VendorType] = Query(None, description="Filter by vendor type"),
    latitude: Optional[float] = Query(None, description="User latitude for distance calculation"),
    longitude: Optional[float] = Query(None, description="User longitude for distance calculation"),
    max_distance: Optional[float] = Query(None, description="Maximum distance in kilometers"),
    limit: int = Query(20, ge=1, le=50, description="Number of trending vendors to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get trending vendors based on recent order activity"""
    
    # For now, we'll simulate trending by getting active vendors
    # In a real implementation, you'd track order counts, ratings, etc.
    vendors_query = db.query(Vendor).filter(Vendor.is_active == True)
    
    if vendor_type:
        vendors_query = vendors_query.filter(Vendor.vendor_type == vendor_type)
    
    vendors = vendors_query.limit(limit * 2).all()  # Get more to filter by distance
    
    # Filter by distance if location provided
    if latitude is not None and longitude is not None and max_distance is not None:
        filtered_vendors = []
        for vendor in vendors:
            if vendor.latitude and vendor.longitude:
                distance = haversine_distance(latitude, longitude, vendor.latitude, vendor.longitude)
                if distance <= max_distance:
                    vendor.distance = distance
                    filtered_vendors.append(vendor)
        vendors = filtered_vendors
    
    # Return limited results
    return vendors[:limit]


@router.get("/trending/items", response_model=List[ItemResponse])
async def get_trending_items(
    category_id: Optional[int] = Query(None, description="Filter by category"),
    vendor_id: Optional[int] = Query(None, description="Filter by vendor"),
    limit: int = Query(20, ge=1, le=50, description="Number of trending items to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get trending menu items based on popularity"""
    
    # Base query - join with vendor to ensure active vendors only
    items_query = db.query(Item).join(Vendor, Item.vendor_id == Vendor.id).filter(
        Item.is_available == True,
        Vendor.is_active == True
    )
    
    if category_id:
        items_query = items_query.filter(Item.category_id == category_id)
    
    if vendor_id:
        items_query = items_query.filter(Item.vendor_id == vendor_id)
    
    # For now, we'll return available items
    # In a real implementation, you'd track order frequency, ratings, etc.
    items = items_query.limit(limit).all()
    
    return items