"""In-memory escalation queue for the human-in-the-loop workflow.

Two queues live here:
  - Medium (agent has proposed a reply; human approves / edits / rejects)
  - High   (agent has NOT acted; human takes over the conversation)

Rationale (Methodology chapter): keeping the two queues separate makes
the human's next action deterministic per queue -- there is no branch on
"which risk tier is this again?" at approval time. The dashboard renders
them in distinct tabs for the same reason.

Persistence: in-memory. Prototype-appropriate. Swap this class for a
DB-backed one later without touching the orchestrator.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


class EscalationItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    conversation_id: str
    rider_id: str
    booking_id: Optional[str] = None

    risk_level: Literal["medium", "high"]
    intent: str

    rider_messages: list[str] = Field(default_factory=list)
    agent_reasoning: str

    # Only set for medium; None for high.
    proposed_reply: Optional[str] = None

    # Set when the human resolves the item.
    status: Literal["pending", "approved", "edited", "rejected", "handled"] = "pending"
    resolved_at: Optional[datetime] = None
    final_reply: Optional[str] = None


class EscalationQueue:
    def __init__(self) -> None:
        self._items: dict[str, EscalationItem] = {}

    # ---------- Adding ----------

    def add_medium(
        self,
        *,
        conversation_id: str,
        rider_id: str,
        booking_id: Optional[str],
        intent: str,
        rider_messages: list[str],
        agent_reasoning: str,
        proposed_reply: str,
    ) -> EscalationItem:
        item = EscalationItem(
            conversation_id=conversation_id,
            rider_id=rider_id,
            booking_id=booking_id,
            risk_level="medium",
            intent=intent,
            rider_messages=rider_messages,
            agent_reasoning=agent_reasoning,
            proposed_reply=proposed_reply,
        )
        self._items[item.id] = item
        return item

    def add_high(
        self,
        *,
        conversation_id: str,
        rider_id: str,
        booking_id: Optional[str],
        intent: str,
        rider_messages: list[str],
        agent_reasoning: str,
    ) -> EscalationItem:
        item = EscalationItem(
            conversation_id=conversation_id,
            rider_id=rider_id,
            booking_id=booking_id,
            risk_level="high",
            intent=intent,
            rider_messages=rider_messages,
            agent_reasoning=agent_reasoning,
            proposed_reply=None,
        )
        self._items[item.id] = item
        return item

    # ---------- Reading ----------

    def list_pending(
        self,
        risk_level: Optional[Literal["medium", "high"]] = None,
    ) -> list[EscalationItem]:
        rows = [i for i in self._items.values() if i.status == "pending"]
        if risk_level:
            rows = [i for i in rows if i.risk_level == risk_level]
        return sorted(rows, key=lambda i: i.created_at)

    def get(self, item_id: str) -> Optional[EscalationItem]:
        return self._items.get(item_id)

    def all(self) -> list[EscalationItem]:
        return sorted(self._items.values(), key=lambda i: i.created_at)

    def counts(self) -> dict[str, int]:
        pending_medium = sum(
            1 for i in self._items.values()
            if i.status == "pending" and i.risk_level == "medium"
        )
        pending_high = sum(
            1 for i in self._items.values()
            if i.status == "pending" and i.risk_level == "high"
        )
        return {
            "pending_medium": pending_medium,
            "pending_high": pending_high,
            "total": len(self._items),
        }

    # ---------- Resolving ----------

    def resolve_medium(
        self,
        item_id: str,
        *,
        action: Literal["approved", "edited", "rejected"],
        final_reply: Optional[str] = None,
    ) -> EscalationItem:
        item = self._items.get(item_id)
        if item is None:
            raise KeyError(f"Escalation {item_id} not found")
        if item.risk_level != "medium":
            raise ValueError(
                f"resolve_medium called on a {item.risk_level}-risk item"
            )
        if item.status != "pending":
            raise ValueError(f"Item is already {item.status}")

        item.status = action
        item.resolved_at = datetime.now(timezone.utc)
        item.final_reply = final_reply if action != "rejected" else None
        return item

    def resolve_high(
        self,
        item_id: str,
        *,
        final_reply: Optional[str] = None,
    ) -> EscalationItem:
        item = self._items.get(item_id)
        if item is None:
            raise KeyError(f"Escalation {item_id} not found")
        if item.risk_level != "high":
            raise ValueError(
                f"resolve_high called on a {item.risk_level}-risk item"
            )
        if item.status != "pending":
            raise ValueError(f"Item is already {item.status}")

        item.status = "handled"
        item.resolved_at = datetime.now(timezone.utc)
        item.final_reply = final_reply
        return item


# Module-level default instance so callers can just import and use.
escalation_queue = EscalationQueue()
