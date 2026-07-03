'''Pydantic models for API request/response bodies.

These are separate from the ORM models (schemas.py) because API shape
should be free to differ from database shape. Kept flat and explicit for
easier consumption by v0 UIs and the agent.
'''
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ---------- Driver ----------

class DriverOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone_number: str
    status: str
    vehicle_type: str
    service_area: Optional[str] = None
    organization: Optional[str] = None
    blocked: bool

    class Config:
        from_attributes = True


class DriverDetailOut(DriverOut):
    '''Driver detail view: adds active tour summary if any.'''
    active_booking_id: Optional[str] = None
    active_booking_summary: Optional[dict] = None


# ---------- Restaurant ----------

class RestaurantOut(BaseModel):
    id: str
    name: str
    address: str
    city: str

    class Config:
        from_attributes = True


# ---------- Booking ----------

class BookingOut(BaseModel):
    id: str
    external_id: str
    status: str
    customer_first_name: Optional[str]
    customer_last_name: Optional[str]
    customer_phone: Optional[str]
    restaurant_id: str
    pickup_address: str
    dropoff_address: str
    driver_id: Optional[str]
    created_at: datetime
    scheduled_at: Optional[datetime]
    delivery_code: str
    retry_status: str
    retry_count: int
    vehicle_type: str

    class Config:
        from_attributes = True


class BookingDetailOut(BookingOut):
    '''Booking detail view: nests restaurant + driver + audit trail summary.'''
    restaurant: Optional[RestaurantOut] = None
    driver: Optional[DriverOut] = None


# ---------- Actions (tool calls the agent will make) ----------

class RedispatchRequest(BaseModel):
    booking_id: str
    reason: str = Field(..., description='Why the booking is being redispatched')


class MarkCompleteRequest(BaseModel):
    booking_id: str
    delivery_code: str
    actor: Literal['AI_AGENT', 'HUMAN_AGENT'] = 'AI_AGENT'


class ActionResult(BaseModel):
    success: bool
    booking_id: str
    new_status: Optional[str] = None
    message: str
