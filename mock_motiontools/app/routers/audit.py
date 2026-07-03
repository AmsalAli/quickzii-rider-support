'''Audit log query endpoints. Read-only.

Powers the Human Agent Dashboard's Audit Log tab and provides the
row-level data source for the Findings chapter evaluation metrics.
'''
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import AuditLogEntry

router = APIRouter(prefix='/audit', tags=['audit'])


@router.get('')
def list_audit(
    booking_id: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    since: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
):
    q = db.query(AuditLogEntry)
    if booking_id:
        q = q.filter(AuditLogEntry.booking_id == booking_id)
    if actor:
        q = q.filter(AuditLogEntry.actor == actor)
    if event_type:
        q = q.filter(AuditLogEntry.event_type == event_type)
    if since:
        q = q.filter(AuditLogEntry.timestamp >= since)

    rows = q.order_by(AuditLogEntry.timestamp.desc()).limit(limit).all()
    return [
        {
            'id': r.id,
            'timestamp': r.timestamp.isoformat(),
            'booking_id': r.booking_id,
            'actor': r.actor,
            'event_type': r.event_type,
            'description': r.description,
            'payload': r.payload_json,
        }
        for r in rows
    ]


@router.get('/summary')
def summary(db: Session = Depends(get_db)):
    '''Aggregate counts by actor and event_type. Useful for the dashboard
    stats pills and as the entry point for Findings-chapter metrics.'''
    from collections import Counter
    all_rows = db.query(AuditLogEntry.actor, AuditLogEntry.event_type).all()
    by_actor = Counter(a for a, _ in all_rows)
    by_event = Counter(e for _, e in all_rows)
    return {
        'total': len(all_rows),
        'by_actor': dict(by_actor),
        'by_event_type': dict(by_event),
    }
