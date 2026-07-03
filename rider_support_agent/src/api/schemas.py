"""HTTP request/response schemas for the rider support agent API.

Kept separate from src/models/schemas.py (which are the agent's internal
data structures). This separation lets the wire format evolve without
touching the orchestrator, and vice versa.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

from src.models.schemas import IntentLabel


# ---------- POST /converse ----------

class ConverseRequest(BaseModel):
    rider_id: str
    conversation_id: str
    booking_id: Optional[str] = None
    text: str
    quick_reply_intent: Optional[IntentLabel] = None


class ConverseResponse(BaseModel):
    conversation_id: str
    reply_text: str
    intent: str
    risk_level: str
    escalated: bool
    escalation_id: Optional[str] = None
    processing_time_ms: float
    tool_calls: list[str] = Field(default_factory=list)


# ---------- GET /escalations/{tier} ----------

class EscalationOut(BaseModel):
    id: str
    created_at: datetime
    conversation_id: str
    rider_id: str
    booking_id: Optional[str]
    risk_level: Literal["medium", "high"]
    intent: str
    rider_messages: list[str]
    agent_reasoning: str
    proposed_reply: Optional[str]
    status: str
    resolved_at: Optional[datetime]
    final_reply: Optional[str]


# ---------- POST /escalations/{id}/resolve-medium ----------

class ResolveMediumRequest(BaseModel):
    action: Literal["approved", "edited", "rejected"]
    final_reply: Optional[str] = None  # required for approved/edited


class ResolveHighRequest(BaseModel):
    final_reply: Optional[str] = None


# ---------- GET /audit ----------

class AuditRow(BaseModel):
    id: str
    timestamp: str
    event_type: str
    actor: str
    conversation_id: Optional[str] = None
    rider_id: Optional[str] = None
    booking_id: Optional[str] = None

    # Free-form additional fields (varies by event_type)
    extra: dict[str, Any] = Field(default_factory=dict)
