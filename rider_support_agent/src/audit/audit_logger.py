"""Append-only JSONL audit logger for the rider support agent.

Every event written here becomes a row in your Chapter 5 dataset.
Design principles:
  - Append-only (never mutate a written row).
  - Write per-event, not batched, so crashes do not lose data.
  - Structured payloads: pandas.read_json(lines=True) reads the whole
    file into a DataFrame with zero preprocessing.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.config.settings import settings


class AuditLogger:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path or settings.audit_log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _write(self, row: dict[str, Any]) -> None:
        row.setdefault("id", str(uuid.uuid4()))
        row.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # ---------- Public API ----------

    def rider_message(self, *, conversation_id: str, rider_id: str,
                      booking_id: Optional[str], text: str,
                      quick_reply_intent: Optional[str] = None) -> None:
        self._write({
            "event_type": "rider_message",
            "actor": "RIDER",
            "conversation_id": conversation_id,
            "rider_id": rider_id,
            "booking_id": booking_id,
            "text": text,
            "quick_reply_intent": quick_reply_intent,
        })

    def intent_classified(self, *, conversation_id: str, rider_id: str,
                          booking_id: Optional[str], intent: str,
                          risk_level: str, reasoning: str,
                          confidence: float) -> None:
        self._write({
            "event_type": "intent_classified",
            "actor": "AI_AGENT",
            "conversation_id": conversation_id,
            "rider_id": rider_id,
            "booking_id": booking_id,
            "intent": intent,
            "risk_level": risk_level,
            "confidence": confidence,
            "reasoning": reasoning,
        })

    def tool_called(self, *, conversation_id: str, rider_id: str,
                    booking_id: Optional[str], tool_name: str,
                    arguments: dict[str, Any], success: bool,
                    result_summary: Optional[str] = None) -> None:
        self._write({
            "event_type": "tool_called",
            "actor": "AI_AGENT",
            "conversation_id": conversation_id,
            "rider_id": rider_id,
            "booking_id": booking_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "success": success,
            "result_summary": result_summary,
        })

    def escalated(self, *, conversation_id: str, rider_id: str,
                  booking_id: Optional[str], risk_level: str,
                  intent: str, summary: str,
                  proposed_reply: Optional[str] = None) -> None:
        self._write({
            "event_type": "escalated",
            "actor": "AI_AGENT",
            "conversation_id": conversation_id,
            "rider_id": rider_id,
            "booking_id": booking_id,
            "risk_level": risk_level,
            "intent": intent,
            "summary": summary,
            "proposed_reply": proposed_reply,
        })

    def conversation_closed(self, *, conversation_id: str, rider_id: str,
                            booking_id: Optional[str], outcome: str,
                            reply_text: str,
                            processing_time_ms: Optional[float] = None,
                            intent: Optional[str] = None) -> None:
        self._write({
            "event_type": "conversation_closed",
            "actor": "AI_AGENT",
            "conversation_id": conversation_id,
            "rider_id": rider_id,
            "booking_id": booking_id,
            "outcome": outcome,
            "intent": intent,
            "reply_text": reply_text,
            "processing_time_ms": processing_time_ms,
        })

    def human_action(self, *, conversation_id: str, rider_id: str,
                     booking_id: Optional[str], action: str,
                     final_reply: Optional[str] = None,
                     original_proposal: Optional[str] = None) -> None:
        """Called when a human reviewer approves/edits/rejects a proposal.
        action in {'approved', 'edited', 'rejected'}.
        """
        self._write({
            "event_type": "human_action",
            "actor": "HUMAN_AGENT",
            "conversation_id": conversation_id,
            "rider_id": rider_id,
            "booking_id": booking_id,
            "action": action,
            "final_reply": final_reply,
            "original_proposal": original_proposal,
        })


# Module-level default instance so callers can just import and use.
audit_logger = AuditLogger()
