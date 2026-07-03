"""Tool executor: bridges Claude's tool_use decisions to real actions.

Every tool the agent can call is routed through this file. Real side
effects happen here:
  - MotionTools API calls (via MotionToolsClient)
  - Escalation queue writes (via EscalationQueue)
  - Audit log rows (via AuditLogger)

Design principle: never let a tool call raise an uncaught exception. If
something fails (HTTP error, bad arguments, missing booking), return
success=False so the orchestrator loop can handle it and Claude can
decide whether to retry, apologise to the rider, or escalate.
"""
from __future__ import annotations
from typing import Any, Optional
from dataclasses import dataclass

from src.audit.audit_logger import audit_logger
from src.escalation.escalation_queue import escalation_queue
from src.clients.motiontools_client import MotionToolsClient, MotionToolsHTTPError
from src.config.settings import settings
from src.models.schemas import (
    IntentLabel, RiskLevel, ClassifiedIntent, ToolCall, ToolResult,
)


@dataclass
class ExecutionContext:
    """State the executor needs about the current conversation.

    Passed in by the orchestrator, not fetched globally, so the executor
    is testable in isolation.
    """
    conversation_id: str
    rider_id: str
    booking_id: Optional[str]           # UUID of the active booking, if any
    booking_external_id: Optional[str]  # short "FFFXTC"-style ID, for user-facing text
    classified_intent: Optional[ClassifiedIntent]
    rider_message_history: list[str]    # plain rider utterances in this session
    # Signals raised by executor for the orchestrator to act on:
    should_close: bool = False
    close_outcome: Optional[str] = None
    close_reply: Optional[str] = None
    escalation_id: Optional[str] = None


class ToolExecutor:
    def __init__(self, motiontools: Optional[MotionToolsClient] = None) -> None:
        self.mt = motiontools or MotionToolsClient()

    # ---------- Public entry point ----------

    def execute(self, call: ToolCall, ctx: ExecutionContext) -> ToolResult:
        """Dispatch a single tool call. Never raises; always returns ToolResult."""
        handler = self._handlers().get(call.tool_name)
        if handler is None:
            result = ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=f"Unknown tool: {call.tool_name}",
            )
            self._log_tool(ctx, call, result, summary="unknown tool")
            return result

        try:
            result = handler(call.arguments, ctx)
        except MotionToolsHTTPError as e:
            result = ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=f"MotionTools API error {e.status_code}: {e.detail}",
            )
        except Exception as e:
            # Absolute catchall. Never let an unexpected exception escape.
            result = ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=f"Unexpected error: {type(e).__name__}: {e}",
            )

        return result

    def _handlers(self) -> dict[str, Any]:
        return {
            "lookup_booking":         self._lookup_booking,
            "share_customer_contact": self._share_customer_contact,
            "start_wait_timer":       self._start_wait_timer,
            "redispatch_booking":     self._redispatch_booking,
            "mark_delivery_complete": self._mark_delivery_complete,
            "propose_human_action":   self._propose_human_action,
            "escalate_to_human":      self._escalate_to_human,
            "send_reply_and_close":   self._send_reply_and_close,
        }

    # ---------- Individual handlers ----------

    def _lookup_booking(self, args: dict, ctx: ExecutionContext) -> ToolResult:
        if not ctx.booking_id:
            return self._done(
                ctx, "lookup_booking", False,
                error="No active booking for this rider.",
                summary="no active booking",
            )
        data = self.mt.get_booking(ctx.booking_id)
        return self._done(
            ctx, "lookup_booking", True, data=data,
            summary=f"fetched {data.get('external_id', ctx.booking_id[:8])}",
        )

    def _share_customer_contact(self, args: dict, ctx: ExecutionContext) -> ToolResult:
        if not ctx.booking_id:
            return self._done(
                ctx, "share_customer_contact", False,
                error="No active booking; cannot share contact.",
                summary="no booking",
            )
        b = self.mt.get_booking(ctx.booking_id)
        first = b.get("customer_first_name") or "the customer"
        phone = b.get("customer_phone") or "(unknown)"
        return self._done(
            ctx, "share_customer_contact", True,
            data={"customer_first_name": first, "customer_phone": phone},
            summary=f"shared contact for booking {b.get('external_id')}",
            call_args=args,
        )

    def _start_wait_timer(self, args: dict, ctx: ExecutionContext) -> ToolResult:
        reason_code = args.get("reason_code", "")
        if reason_code == "order_not_in_restaurant":
            wait_seconds = settings.retry_seconds_order_not_in_resto
        elif reason_code == "order_not_ready":
            wait_seconds = settings.retry_seconds_order_not_ready
        else:
            return self._done(
                ctx, "start_wait_timer", False,
                error=f"Unknown reason_code: {reason_code}",
                summary="bad reason_code",
            )
        if not ctx.booking_id:
            return self._done(
                ctx, "start_wait_timer", False,
                error="No active booking.",
                summary="no booking",
            )
        data = self.mt.start_wait(ctx.booking_id, reason_code, wait_seconds)
        return self._done(
            ctx, "start_wait_timer", True, data=data,
            summary=f"wait started ({wait_seconds}s, {reason_code})",
            call_args=args,
        )

    def _redispatch_booking(self, args: dict, ctx: ExecutionContext) -> ToolResult:
        if not ctx.booking_id:
            return self._done(
                ctx, "redispatch_booking", False,
                error="No active booking.",
                summary="no booking",
            )
        reason = args.get("reason", "Agent-initiated redispatch")
        data = self.mt.redispatch_booking(ctx.booking_id, reason)
        return self._done(
            ctx, "redispatch_booking", True, data=data,
            summary=f"redispatched: {reason[:60]}",
            call_args=args,
        )

    def _mark_delivery_complete(self, args: dict, ctx: ExecutionContext) -> ToolResult:
        if not ctx.booking_id:
            return self._done(
                ctx, "mark_delivery_complete", False,
                error="No active booking.",
                summary="no booking",
            )
        code = str(args.get("delivery_code", "")).strip()
        data = self.mt.mark_complete(ctx.booking_id, code)
        if not data.get("success"):
            return self._done(
                ctx, "mark_delivery_complete", False,
                data=data,
                error=data.get("message", "Wrong code"),
                summary="wrong code",
                call_args=args,
            )
        return self._done(
            ctx, "mark_delivery_complete", True, data=data,
            summary="delivery marked complete",
            call_args=args,
        )

    def _propose_human_action(self, args: dict, ctx: ExecutionContext) -> ToolResult:
        proposed = args.get("proposed_reply", "").strip()
        reasoning = args.get("reasoning", "").strip()
        if not proposed or not reasoning:
            return self._done(
                ctx, "propose_human_action", False,
                error="proposed_reply and reasoning are both required.",
                summary="missing fields",
            )
        intent_str = (ctx.classified_intent.intent.value
                      if ctx.classified_intent else "unknown")
        item = escalation_queue.add_medium(
            conversation_id=ctx.conversation_id,
            rider_id=ctx.rider_id,
            booking_id=ctx.booking_id,
            intent=intent_str,
            rider_messages=ctx.rider_message_history,
            agent_reasoning=reasoning,
            proposed_reply=proposed,
        )
        audit_logger.escalated(
            conversation_id=ctx.conversation_id,
            rider_id=ctx.rider_id,
            booking_id=ctx.booking_id,
            risk_level="medium",
            intent=intent_str,
            summary=reasoning,
            proposed_reply=proposed,
        )
        ctx.escalation_id = item.id
        return self._done(
            ctx, "propose_human_action", True,
            data={"escalation_id": item.id, "risk_level": "medium"},
            summary=f"queued medium escalation {item.id[:8]}",
            call_args=args,
        )

    def _escalate_to_human(self, args: dict, ctx: ExecutionContext) -> ToolResult:
        summary_text = args.get("summary", "").strip()
        holding = args.get("rider_holding_message", "").strip()
        if not summary_text or not holding:
            return self._done(
                ctx, "escalate_to_human", False,
                error="summary and rider_holding_message are both required.",
                summary="missing fields",
            )
        intent_str = (ctx.classified_intent.intent.value
                      if ctx.classified_intent else "unknown")
        item = escalation_queue.add_high(
            conversation_id=ctx.conversation_id,
            rider_id=ctx.rider_id,
            booking_id=ctx.booking_id,
            intent=intent_str,
            rider_messages=ctx.rider_message_history,
            agent_reasoning=summary_text,
        )
        audit_logger.escalated(
            conversation_id=ctx.conversation_id,
            rider_id=ctx.rider_id,
            booking_id=ctx.booking_id,
            risk_level="high",
            intent=intent_str,
            summary=summary_text,
            proposed_reply=None,
        )
        ctx.escalation_id = item.id
        # The holding message is what gets sent to the rider before human takes over.
        ctx.should_close = True
        ctx.close_outcome = "escalated"
        ctx.close_reply = holding
        return self._done(
            ctx, "escalate_to_human", True,
            data={"escalation_id": item.id, "risk_level": "high", "holding_message": holding},
            summary=f"queued high escalation {item.id[:8]}",
            call_args=args,
        )

    def _send_reply_and_close(self, args: dict, ctx: ExecutionContext) -> ToolResult:
        reply = args.get("reply_text", "").strip()
        outcome = args.get("outcome", "resolved")
        if not reply:
            return self._done(
                ctx, "send_reply_and_close", False,
                error="reply_text is required.",
                summary="empty reply",
            )
        ctx.should_close = True
        ctx.close_outcome = outcome
        ctx.close_reply = reply
        return self._done(
            ctx, "send_reply_and_close", True,
            data={"outcome": outcome},
            summary=f"closing with outcome={outcome}",
            call_args=args,
        )

    # ---------- Helper ----------

    def _done(
        self,
        ctx: ExecutionContext,
        tool_name: str,
        success: bool,
        *,
        data: Optional[dict] = None,
        error: Optional[str] = None,
        summary: str = "",
        call_args: Optional[dict] = None,
    ) -> ToolResult:
        result = ToolResult(
            tool_name=tool_name, success=success, data=data, error=error,
        )
        self._log_tool(
            ctx,
            ToolCall(tool_name=tool_name, arguments=call_args or {}),
            result,
            summary=summary,
        )
        return result

    def _log_tool(
        self,
        ctx: ExecutionContext,
        call: ToolCall,
        result: ToolResult,
        *,
        summary: str,
    ) -> None:
        audit_logger.tool_called(
            conversation_id=ctx.conversation_id,
            rider_id=ctx.rider_id,
            booking_id=ctx.booking_id,
            tool_name=call.tool_name,
            arguments=call.arguments,
            success=result.success,
            result_summary=summary or (result.error if not result.success else None),
        )
