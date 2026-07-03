'''Booking endpoints. Read-only from the agent's perspective.

Two endpoints:
  GET /bookings/{booking_id}                -> BookingDetailOut
  GET /bookings/by-external/{external_id}   -> BookingDetailOut
  GET /bookings?status=...&service_area=... -> list[BookingOut]

The by-external lookup exists because riders will typically know the short
'FFFXTC' style ID, not the UUID.
'''
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import Booking, Restaurant, Driver
from app.models.api_schemas import (
    BookingOut, BookingDetailOut, RestaurantOut, DriverOut,
)

router = APIRouter(prefix='/bookings', tags=['bookings'])


def _detail_from(booking: Booking, db: Session) -> BookingDetailOut:
    r = db.query(Restaurant).filter(Restaurant.id == booking.restaurant_id).first()
    d = None
    if booking.driver_id:
        d = db.query(Driver).filter(Driver.id == booking.driver_id).first()

    base = BookingOut.model_validate(booking).model_dump()
    return BookingDetailOut(
        **base,
        restaurant=RestaurantOut.model_validate(r) if r else None,
        driver=DriverOut.model_validate(d) if d else None,
    )


@router.get('', response_model=list[BookingOut])
def list_bookings(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Booking)
    if status:
        q = q.filter(Booking.status == status)
    return q.order_by(Booking.created_at.desc()).limit(limit).all()


@router.get('/{booking_id}', response_model=BookingDetailOut)
def get_booking(booking_id: str, db: Session = Depends(get_db)):
    b = db.query(Booking).filter(Booking.id == booking_id).first()
    if not b:
        raise HTTPException(status_code=404, detail='Booking not found')
    return _detail_from(b, db)


@router.get('/by-external/{external_id}', response_model=BookingDetailOut)
def get_booking_by_external(external_id: str, db: Session = Depends(get_db)):
    b = db.query(Booking).filter(Booking.external_id == external_id).first()
    if not b:
        raise HTTPException(status_code=404, detail='Booking not found')
    return _detail_from(b, db)
