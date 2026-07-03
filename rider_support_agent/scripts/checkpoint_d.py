"""Batch D end-to-end HTTP checkpoint.

Requires BOTH servers running:
  - mock MotionTools on :8001
  - rider support agent on :8002

Exercises every agent endpoint from a client:
  1. GET  /health                             -- server alive
  2. POST /converse    (LOW-risk)             -- rider chat happy path
  3. GET  /audit?conversation_id=...          -- audit rows exist for it
  4. POST /converse    (MEDIUM-risk)          -- creates a medium escalation
  5. GET  /escalations/medium                 -- dashboard queue read
  6. POST /escalations/{id}/resolve-medium    -- human edits & approves
  7. POST /converse    (HIGH-risk, 2 turns)   -- creates a high escalation
  8. GET  /escalations/high                   -- dashboard queue read
  9. POST /escalations/{id}/resolve-high      -- human marks handled
 10. GET  /audit?actor=HUMAN_AGENT            -- human actions logged

Prints PASS/FAIL for each step. This is what confirms the whole system
is callable via HTTP -- the exact shape v0.app UIs will consume.
"""
import sys
import time
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

AGENT = "http://127.0.0.1:8002"
MOCK  = "http://127.0.0.1:8001"


def step(n, label, ok, extra=""):
    marker = "PASS" if ok else "FAIL"
    print(f"[{marker}] Step {n}: {label}" + (f"  --  {extra}" if extra else ""))


# --- Preconditions ---
try:
    r = requests.get(f"{AGENT}/health", timeout=3)
    assert r.status_code == 200
except Exception as e:
    print(f"Agent server not reachable at {AGENT}. Start it with 'python run.py' in a second terminal.")
    print(f"  underlying error: {e}")
    raise SystemExit(1)

try:
    r = requests.get(f"{MOCK}/health", timeout=3)
    assert r.status_code == 200
except Exception as e:
    print(f"Mock MotionTools not reachable at {MOCK}. Start it too.")
    raise SystemExit(1)

# Grab a real en_route booking to test against
bookings = requests.get(f"{MOCK}/bookings?status=en_route&limit=5").json()
if not bookings:
    print("No en_route bookings in mock DB. Reseed first.")
    raise SystemExit(1)

print("Preconditions OK. Running 10 steps.\n")


# --- 1. Health ---
r = requests.get(f"{AGENT}/health")
step(1, "GET /health", r.status_code == 200 and r.json().get("status") == "ok")


# --- 2. POST /converse (LOW-risk) ---
b1 = bookings[0]
conv_low = f"conv-http-low-{uuid.uuid4().hex[:6]}"
r = requests.post(f"{AGENT}/converse", json={
    "rider_id": b1["driver_id"],
    "conversation_id": conv_low,
    "booking_id": b1["id"],
    "text": "I pressed I cannot reach the customer -- they arent picking up.",
    "quick_reply_intent": "customer_unreachable",
})
low_body = r.json() if r.ok else {}
low_ok = (
    r.status_code == 200
    and low_body.get("intent") == "customer_unreachable"
    and low_body.get("risk_level") == "low"
    and not low_body.get("escalated")
    and "share_customer_contact" in low_body.get("tool_calls", [])
)
step(2, "POST /converse (LOW)", low_ok,
     extra=f"reply: {low_body.get('reply_text', '')[:80]}...")


# --- 3. GET /audit filtered by that conversation ---
r = requests.get(f"{AGENT}/audit", params={"conversation_id": conv_low})
audit_rows = r.json() if r.ok else []
event_types = {row.get("event_type") for row in audit_rows}
audit_low_ok = (
    r.status_code == 200
    and "rider_message" in event_types
    and "intent_classified" in event_types
    and "tool_called" in event_types
    and "conversation_closed" in event_types
)
step(3, "GET /audit (filtered by conv)", audit_low_ok,
     extra=f"{len(audit_rows)} rows, types={sorted(event_types)}")


# --- 4. POST /converse (MEDIUM-risk) ---
b2 = bookings[1]
conv_med = f"conv-http-med-{uuid.uuid4().hex[:6]}"
r = requests.post(f"{AGENT}/converse", json={
    "rider_id": b2["driver_id"],
    "conversation_id": conv_med,
    "booking_id": b2["id"],
    "text": "Vehicle breakdown -- chain snapped, about 1km from the drop-off.",
    "quick_reply_intent": "vehicle_breakdown",
})
med_body = r.json() if r.ok else {}
med_ok = (
    r.status_code == 200
    and med_body.get("risk_level") == "medium"
    and med_body.get("escalated") is True
    and med_body.get("escalation_id")
)
step(4, "POST /converse (MEDIUM)", med_ok,
     extra=f"escalation_id={med_body.get('escalation_id', '?')[:8]}...")
med_escalation_id = med_body.get("escalation_id")


# --- 5. GET /escalations/medium ---
r = requests.get(f"{AGENT}/escalations/medium")
med_queue = r.json() if r.ok else []
this_item = next((i for i in med_queue if i["id"] == med_escalation_id), None)
med_queue_ok = (
    r.status_code == 200
    and this_item is not None
    and this_item["status"] == "pending"
    and this_item["proposed_reply"]
)
step(5, "GET /escalations/medium", med_queue_ok,
     extra=f"{len(med_queue)} pending, proposal preview: {(this_item or {}).get('proposed_reply', '')[:60]}...")


# --- 6. POST /escalations/{id}/resolve-medium ---
final_edited = (this_item.get("proposed_reply", "") + " (edited by human)") if this_item else "edited"
r = requests.post(
    f"{AGENT}/escalations/{med_escalation_id}/resolve-medium",
    json={"action": "edited", "final_reply": final_edited},
)
resolve_body = r.json() if r.ok else {}
resolve_med_ok = (
    r.status_code == 200
    and resolve_body.get("status") == "edited"
    and resolve_body.get("final_reply") == final_edited
)
step(6, "POST resolve-medium (edited)", resolve_med_ok,
     extra=f"final status: {resolve_body.get('status')}")


# --- 7. POST /converse (HIGH-risk, 2 turns) ---
b3 = bookings[2]
conv_hi = f"conv-http-hi-{uuid.uuid4().hex[:6]}"

r1 = requests.post(f"{AGENT}/converse", json={
    "rider_id": b3["driver_id"],
    "conversation_id": conv_hi,
    "booking_id": b3["id"],
    "text": "Order is damaged -- box crushed and sauce leaking.",
    "quick_reply_intent": "order_damaged",
})
hi_body1 = r1.json() if r1.ok else {}

hi_escalation_id = hi_body1.get("escalation_id")
hi_turn1_escalated = hi_body1.get("escalated") is True

if not hi_turn1_escalated:
    # Turn 2: rider provides more detail
    r2 = requests.post(f"{AGENT}/converse", json={
        "rider_id": b3["driver_id"],
        "conversation_id": conv_hi,
        "booking_id": b3["id"],
        "text": "Pizza box crushed, drink spilled all over the food, not deliverable.",
    })
    hi_body2 = r2.json() if r2.ok else {}
    hi_escalation_id = hi_body2.get("escalation_id")
    hi_ok = hi_body2.get("escalated") is True and hi_body2.get("risk_level") == "high"
    step(7, "POST /converse (HIGH, 2 turns)", hi_ok,
         extra=f"escalation_id={hi_escalation_id[:8] if hi_escalation_id else '?'}...")
else:
    hi_ok = hi_body1.get("risk_level") == "high"
    step(7, "POST /converse (HIGH, 1 turn)", hi_ok,
         extra=f"escalation_id={hi_escalation_id[:8] if hi_escalation_id else '?'}...")


# --- 8. GET /escalations/high ---
r = requests.get(f"{AGENT}/escalations/high")
hi_queue = r.json() if r.ok else []
this_hi = next((i for i in hi_queue if i["id"] == hi_escalation_id), None)
hi_queue_ok = (
    r.status_code == 200
    and this_hi is not None
    and this_hi["status"] == "pending"
    and this_hi["proposed_reply"] is None
)
step(8, "GET /escalations/high", hi_queue_ok,
     extra=f"{len(hi_queue)} pending")


# --- 9. POST /escalations/{id}/resolve-high ---
r = requests.post(
    f"{AGENT}/escalations/{hi_escalation_id}/resolve-high",
    json={"final_reply": "Refunded customer; rider free to move on. Case closed."},
)
hi_resolve = r.json() if r.ok else {}
resolve_hi_ok = (
    r.status_code == 200
    and hi_resolve.get("status") == "handled"
)
step(9, "POST resolve-high (handled)", resolve_hi_ok,
     extra=f"final status: {hi_resolve.get('status')}")


# --- 10. GET /audit?actor=HUMAN_AGENT ---
r = requests.get(f"{AGENT}/audit", params={"actor": "HUMAN_AGENT"})
human_rows = r.json() if r.ok else []
actions_present = {row.get("extra", {}).get("action") for row in human_rows}
audit_human_ok = (
    r.status_code == 200
    and len(human_rows) >= 2
    and "edited" in actions_present
    and "handled" in actions_present
)
step(10, "GET /audit (HUMAN_AGENT)", audit_human_ok,
     extra=f"{len(human_rows)} rows, actions: {sorted(a for a in actions_present if a)}")


# --- Summary ---
print()
all_ok = all([
    low_ok, audit_low_ok, med_ok, med_queue_ok, resolve_med_ok,
    hi_ok, hi_queue_ok, resolve_hi_ok, audit_human_ok,
])
print("=" * 70)
print(f"BATCH D CHECKPOINT: {'ALL PASS' if all_ok else 'SOME FAILED'}")
print("=" * 70)
