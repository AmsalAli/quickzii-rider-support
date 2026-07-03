'''Pydantic schemas the rider support agent works with internally.

These are the row-level units of analysis for Chapter 5 evaluation:
  - ClassifiedIntent      -> intent accuracy metric
  - AgentResponse         -> per-turn record, aggregates to automation rate,
                             escalation rate, processing time
'''
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = 'low'          # AI handles autonomously
    MEDIUM = 'medium'    # AI proposes, human approves/edits/rejects
    HIGH = 'high'        # AI does not act; human takes over


class IntentLabel(str, Enum):
    '''Closed set of supported rider intents.

    Mapping to quick-reply buttons:
      1. ORDER_NOT_IN_RESTAURANT -> The order is not available in restaurant
      2. ORDER_NOT_READY         -> Order is not ready yet
      3. CUSTOMER_UNREACHABLE    -> I can't reach out to the customer
      4. ORDER_DAMAGED           -> Order is damaged
      5. CANNOT_DELIVER          -> I can't do the delivery
      6. FORGOT_TO_FINISH        -> I forgot to finish the order on the app
      7. CUSTOMER_REFUSED        -> Customer refused to accept the order
      8. VEHICLE_BREAKDOWN       -> Vehicle breakdown
      9. OTHER                   -> Other (free-text, reclassified downstream)
      Fallback:
         UNKNOWN                 -> Classifier could not identify intent
    '''
    ORDER_NOT_IN_RESTAURANT = 'order_not_in_restaurant'
    ORDER_NOT_READY = 'order_not_ready'
    CUSTOMER_UNREACHABLE = 'customer_unreachable'
    ORDER_DAMAGED = 'order_damaged'
    CANNOT_DELIVER = 'cannot_deliver'
    FORGOT_TO_FINISH = 'forgot_to_finish'
    CUSTOMER_REFUSED = 'customer_refused'
    VEHICLE_BREAKDOWN = 'vehicle_breakdown'
    OTHER = 'other'
    UNKNOWN = 'unknown'


class RiderMessage(BaseModel):
    rider_id: str
    conversation_id: str
    booking_id: Optional[str] = None
    text: str
    quick_reply_intent: Optional[IntentLabel] = None  # set only when a quick-reply button was pressed
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClassifiedIntent(BaseModel):
    intent: IntentLabel
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str  # short rationale for audit trail and error analysis


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class AgentResponse(BaseModel):
    '''One full turn of the agent, ready to be logged and returned.'''
    conversation_id: str
    rider_id: str
    intent: ClassifiedIntent
    risk_level: RiskLevel
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    reply_text: str
    escalated: bool = False
    escalation_reason: Optional[str] = None
    processing_time_ms: Optional[float] = None
