'''Driver endpoints. Read-only from the agent's perspective.

Two endpoints:
  GET /drivers/{driver_id}          -> DriverDetailOut (with active booking)
  GET /drivers?service_area=...     -> list[DriverOut]
'''
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import Driver, Booking
from app.models.api_schemas import DriverOut, DriverDetailOut

router = APIRouter(prefix='/drivers', tags=['drivers'])


@router.get('', response_model=list[DriverOut])
def list_drivers(
    service_area: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Driver)
    if service_area:
        q = q.filter(Driver.service_area == service_area)
    if status:
        q = q.filter(Driver.status == status)
    return q.limit(limit).all()


@router.get('/{driver_id}', response_model=DriverDetailOut)
def get_driver(driver_id: str, db: Session = Depends(get_db)):
    d = db.query(Driver).filter(Driver.id == driver_id).first()
    if not d:
        raise HTTPException(status_code=404, detail='Driver not found')

    # Look up the driver's current active booking (en_route)
    active = (
        db.query(Booking)
        .filter(Booking.driver_id == driver_id, Booking.status == 'en_route')
        .first()
    )

    active_summary = None
    active_id = None
    if active:
        active_id = active.id
        active_summary = {
            'external_id': active.external_id,
            'pickup_address': active.pickup_address,
            'dropoff_address': active.dropoff_address,
            'status': active.status,
        }

    return DriverDetailOut(
        **DriverOut.model_validate(d).model_dump(),
        active_booking_id=active_id,
        active_booking_summary=active_summary,
    )
