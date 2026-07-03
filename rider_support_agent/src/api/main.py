"""FastAPI application for the rider support agent.

Six endpoints:
  POST /converse                         -- rider message in, agent reply out
  GET  /escalations/medium               -- pending medium queue
  GET  /escalations/high                 -- pending high queue
  POST /escalations/{id}/resolve-medium  -- human approve/edit/reject
  POST /escalations/{id}/resolve-high    -- human marks a high case handled
  GET  /audit                            -- read the append-only JSONL log
  GET  /health                           -- liveness

CORS is permissive (allow_origins=["*"]) because both the rider chat UI
and the human agent dashboard will call this from a different port during
development. Tighten for any real deployment.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import (
    ConverseRequest, ConverseResponse,
    EscalationOut,
    ResolveMediumRequest, ResolveHighRequest,
    AuditRow,
)
from src.audit.audit_logger import audit_logger
from src.config.settings import settings
from src.escalation.escalation_queue import escalation_queue, EscalationItem
from src.models.schemas import RiderMessage
from src.orchestrator.orchestrator import orchestrator


app = FastAPI(
    title="Rider Support Agent API",
    description=(
        "HTTP surface for the human-in-the-loop rider support agent. "
        "Consumed by the rider chat UI (POST /converse) and the human "
        "agent dashboard (escalations + audit endpoints)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Meta ----------

@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": "rider-support-agent",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


# ---------- Rider chat: single-turn conversation ----------

@app.post("/converse", response_model=ConverseResponse, tags=["rider"])
def converse(req: ConverseRequest) -> ConverseResponse:
    """One rider message in, one agent reply out.

    The orchestrator handles intent classification, risk routing, tool
    calls, and audit logging. This endpoint is a thin adapter.
    """
    msg = RiderMessage(
        rider_id=req.rider_id,
        conversation_id=req.conversation_id,
        booking_id=req.booking_id,
        text=req.text,
        quick_reply_intent=req.quick_reply_intent,
    )
    agent_response = orchestrator.handle_rider_message(msg)

    # If this turn escalated, find the most recent escalation for this convo
    escalation_id: Optional[str] = None
    if agent_response.escalated:
        for item in reversed(escalation_queue.all()):
            if item.conversation_id == req.conversation_id:
                escalation_id = item.id
                break

    return ConverseResponse(
        conversation_id=agent_response.conversation_id,
        reply_text=agent_response.reply_text,
        intent=agent_response.intent.intent.value,
        risk_level=agent_response.risk_level.value,
        escalated=agent_response.escalated,
        escalation_id=escalation_id,
        processing_time_ms=agent_response.processing_time_ms or 0.0,
        tool_calls=[t.tool_name for t in agent_response.tool_calls],
    )


# ---------- Escalations ----------

def _to_out(item: EscalationItem) -> EscalationOut:
    return EscalationOut(**item.model_dump())


@app.get("/escalations/medium", response_model=list[EscalationOut], tags=["dashboard"])
def list_pending_medium(include_resolved: bool = Query(False)) -> list[EscalationOut]:
    """Medium-risk items awaiting human review (approve/edit/reject)."""
    if include_resolved:
        rows = [i for i in escalation_queue.all() if i.risk_level == "medium"]
    else:
        rows = escalation_queue.list_pending("medium")
    return [_to_out(i) for i in rows]


@app.get("/escalations/high", response_model=list[EscalationOut], tags=["dashboard"])
def list_pending_high(include_resolved: bool = Query(False)) -> list[EscalationOut]:
    """High-risk items requiring full human handling."""
    if include_resolved:
        rows = [i for i in escalation_queue.all() if i.risk_level == "high"]
    else:
        rows = escalation_queue.list_pending("high")
    return [_to_out(i) for i in rows]


@app.get("/escalations/{item_id}", response_model=EscalationOut, tags=["dashboard"])
def get_escalation(item_id: str) -> EscalationOut:
    item = escalation_queue.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return _to_out(item)


@app.post(
    "/escalations/{item_id}/resolve-medium",
    response_model=EscalationOut,
    tags=["dashboard"],
)
def resolve_medium(item_id: str, req: ResolveMediumRequest) -> EscalationOut:
    """Human dispatcher approves, edits, or rejects an AI-proposed reply.

    The original proposal and the final (possibly edited) reply are both
    recorded in the audit log so Chapter 5 can measure agreement rate,
    edit rate, and rejection rate.
    """
    item = escalation_queue.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Escalation not found")
    if item.risk_level != "medium":
        raise HTTPException(status_code=400, detail="Item is not medium-risk")
    if item.status != "pending":
        raise HTTPException(status_code=409, detail=f"Already {item.status}")

    if req.action in ("approved", "edited") and not req.final_reply:
        raise HTTPException(
            status_code=400,
            detail="final_reply is required for approved/edited actions",
        )

    original_proposal = item.proposed_reply
    try:
        updated = escalation_queue.resolve_medium(
            item_id, action=req.action, final_reply=req.final_reply,
        )
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    audit_logger.human_action(
        conversation_id=item.conversation_id,
        rider_id=item.rider_id,
        booking_id=item.booking_id,
        action=req.action,
        final_reply=req.final_reply,
        original_proposal=original_proposal,
    )

    return _to_out(updated)


@app.post(
    "/escalations/{item_id}/resolve-high",
    response_model=EscalationOut,
    tags=["dashboard"],
)
def resolve_high(item_id: str, req: ResolveHighRequest) -> EscalationOut:
    """Human dispatcher marks a high-risk case as handled."""
    item = escalation_queue.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Escalation not found")
    if item.risk_level != "high":
        raise HTTPException(status_code=400, detail="Item is not high-risk")
    if item.status != "pending":
        raise HTTPException(status_code=409, detail=f"Already {item.status}")

    try:
        updated = escalation_queue.resolve_high(item_id, final_reply=req.final_reply)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    audit_logger.human_action(
        conversation_id=item.conversation_id,
        rider_id=item.rider_id,
        booking_id=item.booking_id,
        action="handled",
        final_reply=req.final_reply,
        original_proposal=None,
    )

    return _to_out(updated)


# ---------- Audit log ----------

@app.get("/audit", response_model=list[AuditRow], tags=["dashboard"])
def read_audit(
    event_type: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    conversation_id: Optional[str] = Query(None),
    booking_id: Optional[str] = Query(None),
    limit: int = Query(200, le=2000),
) -> list[AuditRow]:
    """Read the append-only JSONL audit log.

    Filters are optional and applied in Python (the log is a flat file,
    not a DB). For dissertation-scale volumes (< 10k rows) this is fine;
    for production you'd move the log to a real database.
    """
    log_path = Path(settings.audit_log_path)
    if not log_path.exists():
        return []

    known_top_fields = {
        "id", "timestamp", "event_type", "actor",
        "conversation_id", "rider_id", "booking_id",
    }

    rows: list[AuditRow] = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event_type and raw.get("event_type") != event_type:
                continue
            if actor and raw.get("actor") != actor:
                continue
            if conversation_id and raw.get("conversation_id") != conversation_id:
                continue
            if booking_id and raw.get("booking_id") != booking_id:
                continue

            extra = {k: v for k, v in raw.items() if k not in known_top_fields}
            rows.append(AuditRow(
                id=raw.get("id", ""),
                timestamp=raw.get("timestamp", ""),
                event_type=raw.get("event_type", ""),
                actor=raw.get("actor", ""),
                conversation_id=raw.get("conversation_id"),
                rider_id=raw.get("rider_id"),
                booking_id=raw.get("booking_id"),
                extra=extra,
            ))

    # Most recent first, capped at limit
    rows.sort(key=lambda r: r.timestamp, reverse=True)
    return rows[:limit]
