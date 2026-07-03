"""Rider support agent orchestrator.

Runtime loop for one rider conversation. Given a rider message (and any
prior turns in the same conversation), the orchestrator:

  1. Classifies intent (from quick_reply_intent if present, else LLM).
  2. Looks up risk tier via the deterministic risk policy.
  3. Feeds the conversation to Claude with tools available.
  4. For each tool_use block Claude returns, dispatches to the executor,
     which mutates real state (MotionTools API, escalation queue, audit
     log) and returns a tool_result.
  5. Feeds tool_results back to Claude, which may produce more tool calls
     or a final text response.
  6. Loops up to max_tool_call_rounds rounds (safety cap).
  7. Returns an AgentResponse summarising the whole turn.

The orchestrator itself has no domain knowledge -- adding a new tool
requires no orchestrator change.
"""
from __future__ import annotations
import time
import uuid
from typing import Any, Optional

from src.agent.claude_client import ClaudeClient
from src.audit.audit_logger import audit_logger
from src.clients.motiontools_client import MotionToolsClient
from src.config.risk_policy import get_risk_level
from src.config.settings import settings
from src.models.schemas import (
    RiderMessage, ClassifiedIntent, IntentLabel, RiskLevel,
    ToolCall, ToolResult, AgentResponse,
)
from src.orchestrator.tool_executor import ToolExecutor, ExecutionContext


# In-memory per-conversation transcript store.
# Structure: conversations[conv_id] = list of Anthropic-format message dicts
# Cleared when the process restarts; that's fine for a prototype.
_conversations: dict[str, list[dict[str, Any]]] = {}


class Orchestrator:
    def __init__(
        self,
        claude: Optional[ClaudeClient] = None,
        executor: Optional[ToolExecutor] = None,
        motiontools: Optional[MotionToolsClient] = None,
    ) -> None:
        self.claude = claude or ClaudeClient()
        self.executor = executor or ToolExecutor(motiontools=motiontools)

    # ---------- Public entry point ----------

    def handle_rider_message(self, msg: RiderMessage) -> AgentResponse:
        """Main entry point: one rider message in, one AgentResponse out."""
        t0 = time.perf_counter()

        # 1. Log the incoming rider message
        audit_logger.rider_message(
            conversation_id=msg.conversation_id,
            rider_id=msg.rider_id,
            booking_id=msg.booking_id,
            text=msg.text,
            quick_reply_intent=(msg.quick_reply_intent.value
                                if msg.quick_reply_intent else None),
        )

        # 2. Classify intent (button > LLM > UNKNOWN)
        intent = self._classify_intent(msg)
        risk = get_risk_level(intent.intent)
        audit_logger.intent_classified(
            conversation_id=msg.conversation_id,
            rider_id=msg.rider_id,
            booking_id=msg.booking_id,
            intent=intent.intent.value,
            risk_level=risk.value,
            confidence=intent.confidence,
            reasoning=intent.reasoning,
        )

        # 3. Build execution context (shared across tool calls this turn)
        ctx = ExecutionContext(
            conversation_id=msg.conversation_id,
            rider_id=msg.rider_id,
            booking_id=msg.booking_id,
            booking_external_id=None,
            classified_intent=intent,
            rider_message_history=self._history_of_rider_texts(
                msg.conversation_id
            ) + [msg.text],
        )

        # 4. Append rider message to the Claude-format transcript
        transcript = _conversations.setdefault(msg.conversation_id, [])
        transcript.append({
            "role": "user",
            "content": self._compose_rider_content(msg, intent, risk),
        })

        # 5. Loop: Claude -> tool_use -> executor -> tool_result -> Claude
        tool_calls_this_turn: list[ToolCall] = []
        tool_results_this_turn: list[ToolResult] = []
        final_text: Optional[str] = None
        rounds_used = 0

        for round_i in range(settings.max_tool_call_rounds):
            rounds_used = round_i + 1
            response = self.claude.send(messages=transcript)

            # Store the assistant turn verbatim so subsequent turns preserve
            # the tool_use/tool_result pairing that Claude's API expects.
            transcript.append({
                "role": "assistant",
                "content": [self._block_to_dict(b) for b in response.content],
            })

            # Collect tool calls, run them, produce a tool_result user turn
            tool_use_blocks = [b for b in response.content
                               if getattr(b, "type", None) == "tool_use"]
            text_blocks = [b for b in response.content
                           if getattr(b, "type", None) == "text"]

            if not tool_use_blocks:
                # Claude produced only text -- treat as final answer
                final_text = "\n\n".join(b.text for b in text_blocks).strip()
                break

            tool_result_blocks: list[dict[str, Any]] = []
            for tub in tool_use_blocks:
                call = ToolCall(
                    tool_name=tub.name,
                    arguments=dict(tub.input) if tub.input else {},
                )
                tool_calls_this_turn.append(call)

                result = self.executor.execute(call, ctx)
                tool_results_this_turn.append(result)

                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tub.id,
                    "content": self._format_tool_result(result),
                    "is_error": not result.success,
                })

                # If the executor signalled closure (send_reply_and_close /
                # escalate_to_human), stop the loop after this batch.
                if ctx.should_close:
                    final_text = ctx.close_reply
                    break

            transcript.append({
                "role": "user",
                "content": tool_result_blocks,
            })

            if ctx.should_close:
                break

            if response.stop_reason == "end_turn":
                # Shouldn't happen if tool_use blocks were present, but be safe
                break

        if final_text is None:
            # Safety-cap hit or no text produced; provide a fallback message
            final_text = (
                "I'm having trouble completing this for you right now. "
                "Let me hand you to a human teammate."
            )
            # Force high-risk escalation as fallback
            self.executor.execute(ToolCall(
                tool_name="escalate_to_human",
                arguments={
                    "summary": "Agent hit max tool-call rounds without resolving.",
                    "rider_holding_message": final_text,
                },
            ), ctx)

        # 6. Log conversation closure
        processing_ms = (time.perf_counter() - t0) * 1000
        audit_logger.conversation_closed(
            conversation_id=msg.conversation_id,
            rider_id=msg.rider_id,
            booking_id=msg.booking_id,
            outcome=ctx.close_outcome or "resolved",
            reply_text=final_text,
            processing_time_ms=processing_ms,
            intent=intent.intent.value,
        )

        return AgentResponse(
            conversation_id=msg.conversation_id,
            rider_id=msg.rider_id,
            intent=intent,
            risk_level=risk,
            tool_calls=tool_calls_this_turn,
            tool_results=tool_results_this_turn,
            reply_text=final_text,
            escalated=(ctx.escalation_id is not None),
            escalation_reason=ctx.classified_intent.reasoning if ctx.escalation_id else None,
            processing_time_ms=processing_ms,
        )

    # ---------- Intent classification ----------

    def _classify_intent(self, msg: RiderMessage) -> ClassifiedIntent:
        """Quick-reply button wins if present; otherwise LLM classifies free text.

        For quick-reply intents, the confidence is 1.0 with reasoning noting
        the button press. Free-text 'OTHER' or missing button gets sent to
        Claude for classification.

        This is the intent-accuracy target in your Chapter 5 evaluation:
        does the button always land on the intended label (should be 100%),
        and does the LLM correctly classify free text (this is the number
        that matters and the one to measure).
        """
        # Button case: closed set of intents, trivial mapping
        if msg.quick_reply_intent is not None and msg.quick_reply_intent != IntentLabel.OTHER:
            return ClassifiedIntent(
                intent=msg.quick_reply_intent,
                confidence=1.0,
                reasoning="Quick-reply button pressed by rider.",
            )

        # Free-text or OTHER: ask Claude to classify
        return self._classify_via_claude(msg.text)

    def _classify_via_claude(self, text: str) -> ClassifiedIntent:
        """Simple one-shot intent classification.

        We send a small dedicated prompt asking Claude to return one of the
        nine intent labels. Kept separate from the tool-using system prompt
        so classification is a deterministic function of the message text.
        """
        import json
        labels = [e.value for e in IntentLabel if e != IntentLabel.UNKNOWN]
        system = (
            "You classify short messages from delivery riders into exactly "
            "one of the following intent labels: "
            + ", ".join(labels) + ". "
            "Return ONLY a JSON object with fields: intent (one of the "
            "labels), confidence (0.0-1.0), reasoning (one short sentence). "
            "No prose outside the JSON."
        )
        # Reuse the Anthropic client directly to bypass the tools/system_prompt
        raw = self.claude._client.messages.create(
            model=settings.claude_model,
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": text}],
        )
        text_out = "".join(
            getattr(b, "text", "") for b in raw.content
            if getattr(b, "type", None) == "text"
        ).strip()

        # Robust JSON parse: extract first {...} substring if there's noise
        start = text_out.find("{")
        end = text_out.rfind("}")
        if start == -1 or end == -1:
            return ClassifiedIntent(
                intent=IntentLabel.UNKNOWN,
                confidence=0.0,
                reasoning="Classifier returned no JSON.",
            )
        try:
            parsed = json.loads(text_out[start:end + 1])
            intent_str = parsed.get("intent", "unknown")
            intent = IntentLabel(intent_str) if intent_str in labels else IntentLabel.UNKNOWN
            confidence = float(parsed.get("confidence", 0.5))
            reasoning = str(parsed.get("reasoning", "")).strip() or "no reasoning"
            return ClassifiedIntent(
                intent=intent,
                confidence=max(0.0, min(1.0, confidence)),
                reasoning=reasoning,
            )
        except Exception as e:
            return ClassifiedIntent(
                intent=IntentLabel.UNKNOWN,
                confidence=0.0,
                reasoning=f"Classifier JSON parse failed: {e}",
            )

    # ---------- Transcript helpers ----------

    def _compose_rider_content(
        self, msg: RiderMessage, intent: ClassifiedIntent, risk: RiskLevel,
    ) -> str:
        """Build the string that gets sent as 'user' to Claude.

        Includes a small hidden preamble so Claude sees classified intent
        and risk tier without the rider seeing them. Keeps the actual
        rider text intact.
        """
        preamble = (
            f"[system context: classified_intent={intent.intent.value}, "
            f"risk_level={risk.value}, "
            f"confidence={intent.confidence:.2f}, "
            f"booking_id={msg.booking_id or 'none'}]"
        )
        return f"{preamble}\n\nRider says: {msg.text}"

    def _history_of_rider_texts(self, conversation_id: str) -> list[str]:
        """Extract prior rider utterances from the transcript for the
        escalation queue's rider_messages field.
        """
        turns = _conversations.get(conversation_id, [])
        out: list[str] = []
        for turn in turns:
            if turn.get("role") != "user":
                continue
            content = turn.get("content")
            if isinstance(content, str):
                # Strip our synthetic preamble if present
                if "Rider says:" in content:
                    out.append(content.split("Rider says:", 1)[1].strip())
                else:
                    out.append(content)
        return out

    def _block_to_dict(self, block: Any) -> dict[str, Any]:
        """Serialise an Anthropic content block into the dict form expected
        when we replay the transcript in the next turn.
        """
        btype = getattr(block, "type", None)
        if btype == "text":
            return {"type": "text", "text": block.text}
        if btype == "tool_use":
            return {
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": dict(block.input) if block.input else {},
            }
        # Unknown block type: pass through best-effort
        return {"type": btype or "unknown"}

    def _format_tool_result(self, result: ToolResult) -> str:
        """Return the string body of a tool_result block, safe for Claude
        to read as part of the next turn's context.
        """
        import json
        if result.success:
            return json.dumps({
                "success": True,
                "data": result.data or {},
            }, ensure_ascii=False)
        return json.dumps({
            "success": False,
            "error": result.error or "Unknown error",
        }, ensure_ascii=False)


# Module-level default instance
orchestrator = Orchestrator()


# ---------- Helper for the eventual API layer (Batch D) ----------

def clear_conversation(conversation_id: str) -> None:
    """Called by the API when a conversation ends, or by tests."""
    _conversations.pop(conversation_id, None)


def get_transcript(conversation_id: str) -> list[dict[str, Any]]:
    """Introspection helper for the dashboard / debugging."""
    return list(_conversations.get(conversation_id, []))
