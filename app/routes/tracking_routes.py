from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import base64

from ..shared.database import get_db
from ..shared.api_key_route import verify_api_key
from ..schemas import OrderTrackingResponse
from ..models import Order, Rider, OrderTracking, OrderStatus, RiderStatus
from ..services.queries import GetOrderByIdQuery, GetOrderByIdQueryHandler


router = APIRouter(
    prefix="/tracking",
    tags=["tracking"]
)


class LiveTrackingResponse(BaseModel):
    order_id: int
    status: str
    rider_id: Optional[int] = None
    rider_name: Optional[str] = None
    rider_phone: Optional[str] = None
    rider_latitude: Optional[float] = None
    rider_longitude: Optional[float] = None
    estimated_arrival: Optional[datetime] = None
    delivery_address: str
    tracking_updates: List[OrderTrackingResponse]


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None


class DeliveryTimeline(BaseModel):
    order_placed: datetime
    order_confirmed: Optional[datetime] = None
    preparation_started: Optional[datetime] = None
    ready_for_pickup: Optional[datetime] = None
    picked_up: Optional[datetime] = None
    out_for_delivery: Optional[datetime] = None
    delivered: Optional[datetime] = None
    current_status: str
    next_expected_status: Optional[str] = None
    estimated_completion: Optional[datetime] = None


class DeliveryProofRequest(BaseModel):
    order_id: int
    delivery_note: Optional[str] = None
    customer_signature: Optional[str] = None  # base64 encoded
    delivery_photo: Optional[str] = None  # base64 encoded


@router.get("/orders/{order_id}/live", response_model=LiveTrackingResponse)
async def get_live_order_tracking(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get live tracking information for an order including rider location"""
    
    # Get order details
    query_handler = GetOrderByIdQueryHandler(db)
    order = query_handler.handle(GetOrderByIdQuery(order_id=order_id))
    
    # Get rider information if assigned
    rider = None
    if order.rider_id:
        rider = db.query(Rider).filter(Rider.id == order.rider_id).first()
    
    # Get all tracking updates for this order
    tracking_updates = db.query(OrderTracking).filter(
        OrderTracking.order_id == order_id
    ).order_by(OrderTracking.timestamp.desc()).all()
    
    # Calculate estimated arrival (simplified)
    estimated_arrival = None
    if order.status == OrderStatus.IN_TRANSIT and rider:
        # In real implementation, you'd calculate based on current location and traffic
        estimated_arrival = datetime.utcnow().replace(microsecond=0)
        estimated_arrival = estimated_arrival.replace(minute=estimated_arrival.minute + 15)
    
    return LiveTrackingResponse(
        order_id=order.id,
        status=order.status.value,
        rider_id=rider.id if rider else None,
        rider_name=rider.full_name if rider else None,
        rider_phone=rider.phone_number if rider else None,
        rider_latitude=rider.current_latitude if rider else None,
        rider_longitude=rider.current_longitude if rider else None,
        estimated_arrival=estimated_arrival,
        delivery_address=order.delivery_address,
        tracking_updates=tracking_updates
    )


@router.post("/riders/{rider_id}/location")
async def update_rider_location(
    rider_id: int,
    location_update: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Update rider's current location for live tracking"""
    
    # Verify rider exists
    rider = db.query(Rider).filter(Rider.id == rider_id).first()
    if not rider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rider not found"
        )
    
    # Update rider location
    rider.current_latitude = location_update.latitude
    rider.current_longitude = location_update.longitude
    rider.updated_at = location_update.timestamp or datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Rider location updated successfully",
        "rider_id": rider_id,
        "latitude": location_update.latitude,
        "longitude": location_update.longitude,
        "timestamp": rider.updated_at
    }


@router.get("/orders/{order_id}/timeline", response_model=DeliveryTimeline)
async def get_delivery_timeline(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get complete delivery timeline with timestamps for each status"""
    
    # Get order
    query_handler = GetOrderByIdQueryHandler(db)
    order = query_handler.handle(GetOrderByIdQuery(order_id=order_id))
    
    # Get all tracking records in chronological order
    tracking_records = db.query(OrderTracking).filter(
        OrderTracking.order_id == order_id
    ).order_by(OrderTracking.timestamp.asc()).all()
    
    # Build timeline from tracking records
    timeline = DeliveryTimeline(
        order_placed=order.created_at,
        current_status=order.status.value,
        next_expected_status=None,
        estimated_completion=None
    )
    
    # Map tracking records to timeline events
    for record in tracking_records:
        if record.status == OrderStatus.ACCEPTED:
            timeline.order_confirmed = record.timestamp
        elif record.status == OrderStatus.PREPARING:
            timeline.preparation_started = record.timestamp
        elif record.status == OrderStatus.READY_FOR_PICKUP:
            timeline.ready_for_pickup = record.timestamp
        elif record.status == OrderStatus.IN_TRANSIT:
            timeline.picked_up = record.timestamp
            timeline.out_for_delivery = record.timestamp
        elif record.status == OrderStatus.DELIVERED:
            timeline.delivered = record.timestamp
    
    # Determine next expected status
    if order.status == OrderStatus.PENDING:
        timeline.next_expected_status = "accepted"
    elif order.status == OrderStatus.ACCEPTED:
        timeline.next_expected_status = "preparing"
    elif order.status == OrderStatus.PREPARING:
        timeline.next_expected_status = "ready_for_pickup"
    elif order.status == OrderStatus.READY_FOR_PICKUP:
        timeline.next_expected_status = "in_transit"
    elif order.status == OrderStatus.IN_TRANSIT:
        timeline.next_expected_status = "delivered"
    
    # Estimate completion time (simplified)
    if order.status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        current_time = datetime.utcnow()
        if order.status == OrderStatus.PENDING:
            timeline.estimated_completion = current_time.replace(minute=current_time.minute + 35)
        elif order.status == OrderStatus.ACCEPTED:
            timeline.estimated_completion = current_time.replace(minute=current_time.minute + 30)
        elif order.status == OrderStatus.PREPARING:
            timeline.estimated_completion = current_time.replace(minute=current_time.minute + 20)
        elif order.status == OrderStatus.READY_FOR_PICKUP:
            timeline.estimated_completion = current_time.replace(minute=current_time.minute + 15)
        elif order.status == OrderStatus.IN_TRANSIT:
            timeline.estimated_completion = current_time.replace(minute=current_time.minute + 10)
    
    return timeline


@router.post("/orders/{order_id}/delivery-proof")
async def upload_delivery_proof(
    order_id: int,
    proof_request: DeliveryProofRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Upload delivery proof including photo and signature"""
    
    # Get order
    query_handler = GetOrderByIdQueryHandler(db)
    order = query_handler.handle(GetOrderByIdQuery(order_id=order_id))
    
    # Verify order is in correct status
    if order.status != OrderStatus.IN_TRANSIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only upload delivery proof for orders in transit"
        )
    
    # Validate base64 encoded data if provided
    try:
        if proof_request.customer_signature:
            base64.b64decode(proof_request.customer_signature)
        if proof_request.delivery_photo:
            base64.b64decode(proof_request.delivery_photo)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 encoded image data"
        )
    
    # In a real implementation, you'd:
    # 1. Save images to cloud storage (AWS S3, etc.)
    # 2. Store file URLs in a delivery_proof table
    # 3. Update order status to delivered
    
    # Update order status to delivered
    order.status = OrderStatus.DELIVERED
    order.updated_at = datetime.utcnow()
    
    # Create final tracking entry
    final_tracking = OrderTracking(
        order_id=order_id,
        status=OrderStatus.DELIVERED,
        latitude=None,  # Could include delivery location
        longitude=None,
        timestamp=datetime.utcnow()
    )
    db.add(final_tracking)
    
    # Update rider status back to available
    if order.rider_id:
        rider = db.query(Rider).filter(Rider.id == order.rider_id).first()
        if rider:
            rider.status = RiderStatus.AVAILABLE
    
    db.commit()
    
    return {
        "message": "Delivery proof uploaded successfully",
        "order_id": order_id,
        "delivery_status": "delivered",
        "proof_submitted": True,
        "delivery_time": order.updated_at,
        "delivery_note": proof_request.delivery_note
    }


@router.get("/orders/{order_id}/status-history")
async def get_order_status_history(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Get complete status change history for an order"""
    
    # Verify order exists
    query_handler = GetOrderByIdQueryHandler(db)
    order = query_handler.handle(GetOrderByIdQuery(order_id=order_id))
    
    # Get all tracking records with additional details
    tracking_records = db.query(OrderTracking).filter(
        OrderTracking.order_id == order_id
    ).order_by(OrderTracking.timestamp.asc()).all()
    
    history = []
    for i, record in enumerate(tracking_records):
        # Calculate duration from previous status
        duration_minutes = None
        if i > 0:
            previous_record = tracking_records[i-1]
            duration = record.timestamp - previous_record.timestamp
            duration_minutes = int(duration.total_seconds() / 60)
        
        history.append({
            "status": record.status.value,
            "timestamp": record.timestamp,
            "duration_from_previous": duration_minutes,
            "location": {
                "latitude": record.latitude,
                "longitude": record.longitude
            } if record.latitude and record.longitude else None
        })
    
    return {
        "order_id": order_id,
        "current_status": order.status.value,
        "total_duration_minutes": int((datetime.utcnow() - order.created_at).total_seconds() / 60) if order.status != OrderStatus.DELIVERED else None,
        "status_history": history
    }


@router.post("/orders/{order_id}/update-status")
async def update_order_tracking_status(
    order_id: int,
    new_status: OrderStatus,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_api_key)
):
    """Update order tracking status (for internal use by vendors/riders)"""
    
    # Get order
    query_handler = GetOrderByIdQueryHandler(db)
    order = query_handler.handle(GetOrderByIdQuery(order_id=order_id))
    
    # Validate status transition (simplified validation)
    valid_transitions = {
        OrderStatus.PENDING: [OrderStatus.ACCEPTED, OrderStatus.REJECTED, OrderStatus.CANCELLED],
        OrderStatus.ACCEPTED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
        OrderStatus.PREPARING: [OrderStatus.READY_FOR_PICKUP, OrderStatus.CANCELLED],
        OrderStatus.READY_FOR_PICKUP: [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
        OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
    }
    
    if order.status in valid_transitions and new_status not in valid_transitions[order.status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {order.status.value} to {new_status.value}"
        )
    
    # Update order status
    order.status = new_status
    order.updated_at = datetime.utcnow()
    
    # Create tracking record
    tracking_record = OrderTracking(
        order_id=order_id,
        status=new_status,
        latitude=latitude,
        longitude=longitude,
        timestamp=datetime.utcnow()
    )
    db.add(tracking_record)
    
    db.commit()
    
    return {
        "message": "Order status updated successfully",
        "order_id": order_id,
        "previous_status": order.status.value if order.status != new_status else None,
        "new_status": new_status.value,
        "timestamp": tracking_record.timestamp
    }