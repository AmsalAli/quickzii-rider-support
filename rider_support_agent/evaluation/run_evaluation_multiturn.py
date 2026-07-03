"""Phase 4 evaluation harness -- multi-turn variant.

For scenarios where the system prompt requires a clarifying question
before an action tool is called (e.g. order_damaged, customer_refused,
forgot_to_finish), the harness sends a scripted second turn providing
the clarification. It then reports:

  - First-turn action rate         (from single-turn run, previous script)
  - Full-flow tool-call correctness (from this multi-turn run)

Both metrics have distinct meanings for Chapter 5:
  * First-turn action rate measures how many intents the agent can
    resolve in one turn without needing rider clarification. Lower
    numbers here reflect intentional safety behaviour, not a defect.
  * Full-flow correctness measures whether the agent, given the
    clarifying information it asked for, calls the right action tool
    by the end of the conversation. This is the number that matches
    real deployment behaviour.
"""
import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import requests

from src.config.settings import settings
from src.models.schemas import RiderMessage, IntentLabel
from src.orchestrator.orchestrator import Orchestrator, clear_conversation

MT_BASE = settings.motiontools_base_url

# Scripted second-turn clarifications keyed by scenario ID.
# Only defined for scenarios where the first turn is expected to
# ask a clarifying question before acting.
FOLLOWUPS: dict[str, str] = {
    "T04": "Yes I confirmed with the restaurant staff, they have no record of this order.",
    "T05": "The delivery confirmation code was 1234.",
    "T08": "The pizza box is crushed and there's sauce leaking out. Definitely not deliverable.",
    "T09": "The customer says the food is cold and refuses to accept it.",
    "T12": "Sauce has leaked through the packaging and onto the box lid. Not deliverable.",
}


def get_test_booking():
    r = requests.get(f"{MT_BASE}/bookings?status=en_route&limit=1")
    r.raise_for_status()
    bookings = r.json()
    if not bookings:
        raise SystemExit("No en_route bookings. Reseed the mock DB first.")
    return bookings[0]


def load_scenarios():
    path = Path(__file__).parent / "test_messages.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_multi_turn(orch, scenario, booking, run_id):
    conv_id = f"eval-mt-{run_id}-{scenario['id']}"
    quick = scenario.get("quick_reply_intent")

    # ---- Turn 1 ----
    msg1 = RiderMessage(
        rider_id=booking["driver_id"] or "eval-rider",
        conversation_id=conv_id,
        booking_id=booking["id"],
        text=scenario["text"],
        quick_reply_intent=IntentLabel(quick) if quick else None,
    )
    t0 = time.perf_counter()
    resp1 = orch.handle_rider_message(msg1)
    tools_turn1 = [t.tool_name for t in resp1.tool_calls]

    # ---- Turn 2 if scripted (rider provides clarification) ----
    tools_turn2: list[str] = []
    followup_used = False
    if scenario["id"] in FOLLOWUPS:
        msg2 = RiderMessage(
            rider_id=booking["driver_id"] or "eval-rider",
            conversation_id=conv_id,
            booking_id=booking["id"],
            text=FOLLOWUPS[scenario["id"]],
            quick_reply_intent=None,
        )
        resp2 = orch.handle_rider_message(msg2)
        tools_turn2 = [t.tool_name for t in resp2.tool_calls]
        followup_used = True
        final_resp = resp2
    else:
        final_resp = resp1

    elapsed_ms = (time.perf_counter() - t0) * 1000
    all_tools = tools_turn1 + tools_turn2
    expected_any = set(scenario["expected_tools_any_of"])

    result = {
        "scenario_id": scenario["id"],
        "expected_intent": scenario["expected_intent"],
        "expected_risk": scenario["expected_risk"],
        "expected_tools": sorted(expected_any),
        "actual_intent_final": final_resp.intent.intent.value,
        "actual_risk_final": final_resp.risk_level.value,
        "tools_turn1": tools_turn1,
        "tools_turn2": tools_turn2,
        "tools_all": all_tools,
        "followup_used": followup_used,
        "escalated": final_resp.escalated,
        "total_ms": round(elapsed_ms, 1),
        "first_turn_tool_hit": bool(expected_any & set(tools_turn1)),
        "full_flow_tool_hit":  bool(expected_any & set(all_tools)),
        "intent_correct": final_resp.intent.intent.value == scenario["expected_intent"],
        "risk_correct":   final_resp.risk_level.value   == scenario["expected_risk"],
    }
    clear_conversation(conv_id)
    return result


def report(results):
    df = pd.DataFrame(results)
    n = len(df)

    print("\n" + "=" * 72)
    print(f"MULTI-TURN EVALUATION REPORT  ({n} scenarios)")
    print("=" * 72)

    print(f"\nIntent classification accuracy: {df['intent_correct'].mean():.1%}")
    print(f"Risk-tier accuracy:             {df['risk_correct'].mean():.1%}")

    print("\nTool-call correctness (two views):")
    print(f"  First-turn action rate:        {df['first_turn_tool_hit'].mean():.1%}")
    print(f"    (fraction resolved in one turn without needing clarification)")
    print(f"  Full-flow tool-call correctness: {df['full_flow_tool_hit'].mean():.1%}")
    print(f"    (fraction where the correct tool was called by end of dialogue)")

    print(f"\nAverage total processing time:  {df['total_ms'].mean():.0f} ms")
    print(f"Median total processing time:   {df['total_ms'].median():.0f} ms")

    print(f"\nScenarios that needed a scripted follow-up: "
          f"{df['followup_used'].sum()} of {n} ({df['followup_used'].mean():.0%})")

    print("\nAutomation rate by expected risk tier (full flow):")
    for tier in ["low", "medium", "high"]:
        sub = df[df["expected_risk"] == tier]
        if len(sub) == 0:
            continue
        auto = (~sub["escalated"]).mean()
        print(f"  {tier:6s}  {len(sub):2d} scenarios   "
              f"automated: {auto:.0%}   escalated: {sub['escalated'].mean():.0%}")

    print("\nPer-scenario detail:")
    for _, row in df.iterrows():
        marks = "".join([
            "I" if row["intent_correct"] else "-",
            "R" if row["risk_correct"] else "-",
            "1" if row["first_turn_tool_hit"] else "-",
            "F" if row["full_flow_tool_hit"] else "-",
        ])
        fu = " +FU" if row["followup_used"] else ""
        print(f"  {row['scenario_id']}  [{marks}]{fu:4s}  "
              f"{row['expected_intent']:24s}  "
              f"all_tools={row['tools_all']}")

    print("\nLegend: I=intent R=risk 1=first-turn tool F=full-flow tool  FU=followup used")
    return df


def main():
    scenarios = load_scenarios()
    booking = get_test_booking()
    print(f"Running {len(scenarios)} multi-turn scenarios against booking {booking['external_id']}\n")

    orch = Orchestrator()
    run_id = uuid.uuid4().hex[:6]
    results = []
    for i, s in enumerate(scenarios, 1):
        needs_fu = s["id"] in FOLLOWUPS
        tag = " (2 turns)" if needs_fu else " (1 turn)"
        print(f"  [{i:2d}/{len(scenarios)}] {s['id']}{tag}  {s['text'][:55]}...", flush=True)
        try:
            results.append(run_multi_turn(orch, s, booking, run_id))
        except Exception as e:
            print(f"    ERROR: {type(e).__name__}: {e}")
            results.append({
                "scenario_id": s["id"],
                "expected_intent": s["expected_intent"],
                "expected_risk": s["expected_risk"],
                "expected_tools": sorted(s["expected_tools_any_of"]),
                "actual_intent_final": "error",
                "actual_risk_final": "error",
                "tools_turn1": [], "tools_turn2": [], "tools_all": [],
                "followup_used": False, "escalated": False,
                "total_ms": 0.0,
                "first_turn_tool_hit": False, "full_flow_tool_hit": False,
                "intent_correct": False, "risk_correct": False,
            })

    df = report(results)

    out = Path(__file__).parent / f"results_multiturn_{run_id}.csv"
    df.to_csv(out, index=False)
    print(f"\nResults CSV: {out}")


if __name__ == "__main__":
    main()
