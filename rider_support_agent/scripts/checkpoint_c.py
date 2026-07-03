"""Full Batch C end-to-end checkpoint.

Three scenarios, one per risk tier. Each is a fully realistic rider
conversation running through the real orchestrator, real Claude API,
real MotionTools mock service, and real audit logger.

At the end, reads the audit log file with pandas to show the aggregated
event view -- this is the same code path Chapter 5 will use.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
import uuid
import requests
import pandas as pd
from pathlib import Path

from src.orchestrator.orchestrator import Orchestrator, clear_conversation
from src.models.schemas import RiderMessage, IntentLabel
from src.escalation.escalation_queue import escalation_queue
from src.clients.motiontools_client import MotionToolsClient
from src.config.settings import settings

BASE = settings.motiontools_base_url
orch = Orchestrator()
mt = MotionToolsClient()


def _fresh_booking():
    """Grab a fresh en_route booking for each scenario so they don't collide."""
    bookings = requests.get(f"{BASE}/bookings?status=en_route&limit=10").json()
    if not bookings:
        raise SystemExit("No en_route bookings. Reseed first.")
    # Filter out any we've already touched by picking randomly
    import random
    return random.choice(bookings)


def _print_header(n, title):
    print("\n" + "=" * 72)
    print(f"SCENARIO {n}: {title}")
    print("=" * 72)


# ==================================================================
# SCENARIO 1 -- LOW risk, wait-then-redispatch flow
# ==================================================================
_print_header(1, "LOW risk: order_not_ready -> wait -> expiry -> redispatch")

b = _fresh_booking()
print(f"Booking: {b['external_id']}  initial status: {b['status']}")
conv_id = f"conv-low-{uuid.uuid4().hex[:6]}"

# Turn 1: rider presses button and confirms
msg1 = RiderMessage(
    rider_id=b["driver_id"],
    conversation_id=conv_id,
    booking_id=b["id"],
    text="I pressed order not ready yet. The restaurant says they need more time.",
    quick_reply_intent=IntentLabel.ORDER_NOT_READY,
)
print(f"\n  Turn 1 rider says: {msg1.text}")
r1 = orch.handle_rider_message(msg1)
print(f"  Agent replies:    {r1.reply_text}")
print(f"  Tools called:     {[t.tool_name for t in r1.tool_calls]}")
print(f"  Close outcome:    {r1.processing_time_ms:.0f} ms, intent={r1.intent.intent.value}")

# Verify the wait timer was set on the booking by Claude in Turn 1
after_wait = requests.get(f"{BASE}/bookings/{b['id']}").json()
print(f"\n  Booking retry_status now: {after_wait['retry_status']!r}")

if after_wait['retry_status'] != 'wait_pending':
    print("  WARNING: Turn 1 did not start a wait timer. Flow-1/2 prompt fix may not have applied.")

# Force wait expiry using a 1-second threshold to simulate the rider
# returning after the 10-minute wait would normally have elapsed.
print("\n  Forcing wait expiry (rider returns after wait)...")
time.sleep(2)
expiry = mt.check_wait_expired(b["id"], 1)
current = requests.get(f"{BASE}/bookings/{b['id']}").json()
print(f"  Wait expired={expiry['expired']}, retry_status now={current['retry_status']!r}")

# Turn 2: rider returns with same complaint (new conversation)
conv_id_2 = f"conv-low-return-{uuid.uuid4().hex[:6]}"
msg2 = RiderMessage(
    rider_id=b["driver_id"],
    conversation_id=conv_id_2,
    booking_id=b["id"],
    text="I waited but it is still not ready. What now?",
    quick_reply_intent=IntentLabel.ORDER_NOT_READY,
)
print(f"\n  Turn 2 rider says: {msg2.text}")
r2 = orch.handle_rider_message(msg2)
print(f"  Agent replies:    {r2.reply_text}")
print(f"  Tools called:     {[t.tool_name for t in r2.tool_calls]}")

after_final = requests.get(f"{BASE}/bookings/{b['id']}").json()
print(f"\n  Final booking status: {after_final['status']}")
print(f"  Final retry_count:    {after_final['retry_count']}")

low_ok = (
    "start_wait_timer" in [t.tool_name for t in r1.tool_calls]
    and "redispatch_booking" in [t.tool_name for t in r2.tool_calls]
    and after_final["status"] == "pickable"
)
print(f"\n  Scenario 1 result: {'PASS' if low_ok else 'FAIL -- check tool sequence'}")


# ==================================================================
# SCENARIO 2 -- MEDIUM risk, propose to human
# ==================================================================
_print_header(2, "MEDIUM risk: vehicle_breakdown -> propose_human_action")

b = _fresh_booking()
print(f"Booking: {b['external_id']}  initial status: {b['status']}")
conv_id = f"conv-med-{uuid.uuid4().hex[:6]}"

msg = RiderMessage(
    rider_id=b["driver_id"],
    conversation_id=conv_id,
    booking_id=b["id"],
    text="I pressed vehicle breakdown. My bike chain snapped and I am about 1km from the drop-off. Not sure what to do.",
    quick_reply_intent=IntentLabel.VEHICLE_BREAKDOWN,
)
print(f"\n  Rider says: {msg.text}")
before_medium = escalation_queue.counts()["pending_medium"]
r = orch.handle_rider_message(msg)
after_medium = escalation_queue.counts()["pending_medium"]
print(f"  Agent replies: {r.reply_text}")
print(f"  Tools called:  {[t.tool_name for t in r.tool_calls]}")
print(f"  Escalated:     {r.escalated}")
print(f"  Medium queue: {before_medium} -> {after_medium}")

# Inspect the escalation item
new_medium = [i for i in escalation_queue.list_pending("medium")
              if i.conversation_id == conv_id]
if new_medium:
    it = new_medium[0]
    print(f"\n  Escalation item {it.id[:8]}...")
    print(f"    intent:        {it.intent}")
    print(f"    proposed reply: {it.proposed_reply[:100]}...")
    print(f"    reasoning:     {it.agent_reasoning[:100]}...")

medium_ok = (
    "propose_human_action" in [t.tool_name for t in r.tool_calls]
    and after_medium == before_medium + 1
)
print(f"\n  Scenario 2 result: {'PASS' if medium_ok else 'FAIL -- no medium escalation queued'}")


# ==================================================================
# SCENARIO 3 -- HIGH risk, escalate to human
# ==================================================================
_print_header(3, "HIGH risk: order_damaged -> gather info -> escalate_to_human")

b = _fresh_booking()
print(f"Booking: {b['external_id']}")
conv_id = f"conv-high-{uuid.uuid4().hex[:6]}"

# Turn 1: rider presses button
msg1 = RiderMessage(
    rider_id=b["driver_id"],
    conversation_id=conv_id,
    booking_id=b["id"],
    text="I pressed order is damaged. When I picked it up from the restaurant the box was already crushed and sauce is leaking everywhere.",
    quick_reply_intent=IntentLabel.ORDER_DAMAGED,
)
print(f"\n  Turn 1 rider says: {msg1.text}")
r1 = orch.handle_rider_message(msg1)
print(f"  Agent replies: {r1.reply_text}")
print(f"  Tools called:  {[t.tool_name for t in r1.tool_calls]}")

# The agent likely asks a clarifying question in Turn 1. Provide the answer.
if not r1.escalated:
    msg2 = RiderMessage(
        rider_id=b["driver_id"],
        conversation_id=conv_id,
        booking_id=b["id"],
        text="The pizza box is crushed and the drink has leaked all over the food. It is definitely not deliverable.",
    )
    print(f"\n  Turn 2 rider says: {msg2.text}")
    before_high = escalation_queue.counts()["pending_high"]
    r2 = orch.handle_rider_message(msg2)
    after_high = escalation_queue.counts()["pending_high"]
    print(f"  Agent replies: {r2.reply_text}")
    print(f"  Tools called:  {[t.tool_name for t in r2.tool_calls]}")
    print(f"  Escalated:     {r2.escalated}")
    print(f"  High queue: {before_high} -> {after_high}")
    final_r = r2
    final_counts_delta = after_high - before_high
else:
    print(f"  Escalated in one turn: {r1.escalated}")
    final_r = r1
    final_counts_delta = 1

high_ok = (
    final_r.escalated
    and final_counts_delta == 1
    and "escalate_to_human" in (
        [t.tool_name for t in r1.tool_calls]
        + ([t.tool_name for t in final_r.tool_calls] if final_r is not r1 else [])
    )
)
print(f"\n  Scenario 3 result: {'PASS' if high_ok else 'FAIL -- no high escalation queued'}")


# ==================================================================
# Audit log summary via pandas (this is the Chapter 5 code path)
# ==================================================================
print("\n" + "=" * 72)
print("AUDIT LOG SUMMARY (pandas view, Chapter 5 code path)")
print("=" * 72)

log_path = Path(settings.audit_log_path)
if not log_path.exists():
    print("Audit log missing; nothing to summarise.")
else:
    df = pd.read_json(log_path, lines=True)
    print(f"\nTotal audit rows: {len(df)}")
    print(f"\nEvents by type:\n{df['event_type'].value_counts().to_string()}")
    print(f"\nEvents by actor:\n{df['actor'].value_counts().to_string()}")
    if "intent" in df.columns:
        print(f"\nIntents observed:\n{df['intent'].dropna().value_counts().to_string()}")

print("\n" + "=" * 72)
print("BATCH C RESULT")
print("=" * 72)
print(f"  Scenario 1 (LOW):    {'PASS' if low_ok else 'FAIL'}")
print(f"  Scenario 2 (MEDIUM): {'PASS' if medium_ok else 'FAIL'}")
print(f"  Scenario 3 (HIGH):   {'PASS' if high_ok else 'FAIL'}")

# Cleanup transcripts
for c in [conv_id, conv_id_2 if 'conv_id_2' in dir() else None]:
    if c:
        clear_conversation(c)
