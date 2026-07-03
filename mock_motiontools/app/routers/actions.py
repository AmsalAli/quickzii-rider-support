'''Operational action endpoints. Write-side of the mock MotionTools API.

Each endpoint:
  - Mutates a booking's state
  - Writes an AuditLogEntry recording who did what and why
  - Returns a structured ActionResult the caller can inspect

These are the endpoints the AI agent will invoke as tools during a
rider conversation. Every call is auditable and reversible in principle.
'''
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import Booking, AuditLogEntry
from app.models.api_schemas import (
    RedispatchRequest, MarkCompleteRequest, ActionResult,
)

router = APIRouter(prefix='/actions', tags=['actions'])


def _log(db: Session, *, actor: str, event_type: str, description: str,
         booking_id: str | None = None, payload: dict | None = None) -> None:
    db.add(AuditLogEntry(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        booking_id=booking_id,
        actor=actor,
        event_type=event_type,
        description=description,
        payload_json=payload,
    ))


@router.post('/redispatch', response_model=ActionResult)
def redispatch_booking(req: RedispatchRequest, db: Session = Depends(get_db)):
    b = db.query(Booking).filter(Booking.id == req.booking_id).first()
    if not b:
        raise HTTPException(status_code=404, detail='Booking not found')

    previous_status = b.status
    if b.status in ('paid', 'cancelled'):
        raise HTTPException(
            status_code=409,
            detail=f'Cannot redispatch booking in status {b.status}',
        )

    # Unassign current driver, put back into pickable state
    previous_driver_id = b.driver_id
    b.driver_id = None
    b.status = 'pickable'
    b.retry_status = 'redispatched'
    b.retry_count = (b.retry_count or 0) + 1

    _log(
        db,
        actor='AI_AGENT',
        event_type='booking_redispatched',
        description=f'Booking {b.external_id} redispatched. Reason: {req.reason}',
        booking_id=b.id,
        payload={
            'previous_status': previous_status,
            'previous_driver_id': previous_driver_id,
            'reason': req.reason,
            'retry_count': b.retry_count,
        },
    )
    db.commit()

    return ActionResult(
        success=True,
        booking_id=b.id,
        new_status=b.status,
        message=f'Booking {b.external_id} redispatched successfully',
    )


@router.post('/mark-complete', response_model=ActionResult)
def mark_complete(req: MarkCompleteRequest, db: Session = Depends(get_db)):
    b = db.query(Booking).filter(Booking.id == req.booking_id).first()
    if not b:
        raise HTTPException(status_code=404, detail='Booking not found')

    # Verification against real code (dissertation-defensible choice).
    if req.delivery_code.strip() != b.delivery_code:
        _log(
            db,
            actor=req.actor,
            event_type='mark_complete_rejected',
            description=f'Wrong delivery code supplied for booking {b.external_id}',
            booking_id=b.id,
            payload={'supplied_code': req.delivery_code, 'expected_code': '****'},
        )
        db.commit()
        raise HTTPException(status_code=400, detail='Delivery code does not match')

    b.status = 'paid'
    b.completed_at = datetime.now(timezone.utc)

    _log(
        db,
        actor=req.actor,
        event_type='booking_completed',
        description=f'Booking {b.external_id} marked complete via delivery code verification',
        booking_id=b.id,
        payload={'code_verified': True},
    )
    db.commit()

    return ActionResult(
        success=True,
        booking_id=b.id,
        new_status='paid',
        message='Delivery confirmed and booking marked complete',
    )


# ---------- Wait-timer endpoints (added for agent's retry state machine) ----------

from pydantic import BaseModel
from datetime import timedelta


class StartWaitRequest(BaseModel):
    booking_id: str
    reason_code: str  # 'order_not_in_restaurant' | 'order_not_ready'
    wait_seconds: int  # agent supplies this based on its timing_mode


@router.post('/start-wait', response_model=ActionResult)
def start_wait(req: StartWaitRequest, db: Session = Depends(get_db)):
    b = db.query(Booking).filter(Booking.id == req.booking_id).first()
    if not b:
        raise HTTPException(status_code=404, detail='Booking not found')

    if b.status in ('paid', 'cancelled'):
        raise HTTPException(
            status_code=409,
            detail=f'Cannot start wait on booking in status {b.status}',
        )

    b.retry_status = 'wait_pending'
    b.retry_started_at = datetime.now(timezone.utc)
    # Note: we do not persist wait_seconds; the check-expiry endpoint
    # is told the threshold by the caller.

    _log(
        db,
        actor='AI_AGENT',
        event_type='wait_timer_started',
        description=f'Wait timer started on {b.external_id} ({req.reason_code}, {req.wait_seconds}s)',
        booking_id=b.id,
        payload={'reason_code': req.reason_code, 'wait_seconds': req.wait_seconds},
    )
    db.commit()

    return ActionResult(
        success=True,
        booking_id=b.id,
        new_status=b.status,
        message=f'Wait timer started ({req.wait_seconds}s)',
    )


class CheckWaitRequest(BaseModel):
    booking_id: str
    wait_seconds: int


@router.post('/check-wait-expired')
def check_wait_expired(req: CheckWaitRequest, db: Session = Depends(get_db)):
    b = db.query(Booking).filter(Booking.id == req.booking_id).first()
    if not b:
        raise HTTPException(status_code=404, detail='Booking not found')

    if b.retry_status != 'wait_pending' or b.retry_started_at is None:
        return {
            'booking_id': b.id,
            'has_pending_wait': False,
            'expired': False,
        }

    # NOTE on tzinfo: SQLite loses timezone information on datetime storage,
    # so retry_started_at may come back naive. Normalise both sides.
    started = b.retry_started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    expired = elapsed >= req.wait_seconds

    if expired:
        b.retry_status = 'wait_expired'
        db.commit()

    return {
        'booking_id': b.id,
        'has_pending_wait': True,
        'expired': expired,
        'elapsed_seconds': int(elapsed),
        'threshold_seconds': req.wait_seconds,
    }
