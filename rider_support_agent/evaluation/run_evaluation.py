"""Phase 4 evaluation harness.

Reads evaluation/test_messages.json, runs each scenario through the
orchestrator against real backend state, then reads data/logs/action_log.jsonl
with pandas and reports the Chapter 5 metrics:

  - Intent classification accuracy
  - Risk-tier accuracy
  - Tool-call correctness (was any expected tool actually called)
  - Automation rate (LOW-risk resolved without escalation)
  - Escalation rate by risk tier
  - Average processing time
  - Distribution of outcomes

Usage:
    python evaluation/run_evaluation.py
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


def get_test_booking():
    """Fetch one en_route booking to attach to all scenarios."""
    r = requests.get(f"{MT_BASE}/bookings?status=en_route&limit=1")
    r.raise_for_status()
    bookings = r.json()
    if not bookings:
        raise SystemExit("No en_route bookings. Reseed the mock DB first.")
    return bookings[0]


def load_scenarios():
    path = Path(__file__).parent / "test_messages.json"
    return json.loads(path.read_text(encoding="utf-8"))


def run_scenario(orch, scenario, booking, run_id):
    conv_id = f"eval-{run_id}-{scenario['id']}"
    quick = scenario.get("quick_reply_intent")
    msg = RiderMessage(
        rider_id=booking["driver_id"] or "eval-rider",
        conversation_id=conv_id,
        booking_id=booking["id"],
        text=scenario["text"],
        quick_reply_intent=IntentLabel(quick) if quick else None,
    )
    t0 = time.perf_counter()
    resp = orch.handle_rider_message(msg)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    called_tools = [t.tool_name for t in resp.tool_calls]
    expected_any = set(scenario["expected_tools_any_of"])
    tool_hit = bool(expected_any & set(called_tools))

    result = {
        "scenario_id": scenario["id"],
        "conversation_id": conv_id,
        "text": scenario["text"],
        "quick_reply": quick,
        "expected_intent": scenario["expected_intent"],
        "expected_risk": scenario["expected_risk"],
        "expected_tools": sorted(expected_any),
        "actual_intent": resp.intent.intent.value,
        "actual_risk": resp.risk_level.value,
        "actual_tools": called_tools,
        "escalated": resp.escalated,
        "processing_ms": round(elapsed_ms, 1),
        "intent_correct": resp.intent.intent.value == scenario["expected_intent"],
        "risk_correct": resp.risk_level.value == scenario["expected_risk"],
        "tool_correct": tool_hit,
    }
    clear_conversation(conv_id)
    return result


def report(results):
    df = pd.DataFrame(results)
    n = len(df)

    print("\n" + "=" * 72)
    print(f"EVALUATION REPORT  ({n} scenarios)")
    print("=" * 72)

    print(f"\nIntent classification accuracy: {df['intent_correct'].mean():.1%}")
    print(f"Risk-tier accuracy:             {df['risk_correct'].mean():.1%}")
    print(f"Tool-call correctness:          {df['tool_correct'].mean():.1%}")

    print(f"\nAverage processing time:        {df['processing_ms'].mean():.0f} ms")
    print(f"Median processing time:         {df['processing_ms'].median():.0f} ms")

    print("\nAutomation rate by expected risk tier:")
    for tier in ["low", "medium", "high"]:
        sub = df[df["expected_risk"] == tier]
        if len(sub) == 0:
            continue
        auto = (~sub["escalated"]).mean()
        print(f"  {tier:6s}  {len(sub):2d} scenarios   "
              f"automated: {auto:.0%}   escalated: {sub['escalated'].mean():.0%}")

    print("\nIntent confusion (expected -> actual):")
    conf = df.groupby(["expected_intent", "actual_intent"]).size().reset_index(name="n")
    for _, row in conf.iterrows():
        mark = "OK " if row["expected_intent"] == row["actual_intent"] else "MIS"
        print(f"  [{mark}] {row['expected_intent']:28s} -> {row['actual_intent']:28s}  ({row['n']})")

    print("\nPer-scenario detail:")
    for _, row in df.iterrows():
        marks = "".join([
            "I" if row["intent_correct"] else "-",
            "R" if row["risk_correct"] else "-",
            "T" if row["tool_correct"] else "-",
        ])
        print(f"  {row['scenario_id']}  [{marks}]  "
              f"{row['expected_intent']:24s}  "
              f"tools={row['actual_tools']}")

    return df


def dump_from_audit_log():
    """Also read the persisted audit log and report aggregate stats.

    This is the reproducible-from-disk view your Methodology chapter refers to:
    metrics can be regenerated at any time without rerunning the agent.
    """
    log_path = Path(settings.audit_log_path)
    if not log_path.exists():
        print("\n(no audit log on disk)")
        return
    df = pd.read_json(log_path, lines=True)
    print("\n" + "=" * 72)
    print(f"AUDIT LOG VIEW  ({len(df)} total rows across all runs)")
    print("=" * 72)
    print("\nEvents by type:")
    print(df["event_type"].value_counts().to_string())
    print("\nEvents by actor:")
    print(df["actor"].value_counts().to_string())
    if "intent" in df.columns:
        print("\nIntents observed in audit log:")
        print(df["intent"].dropna().value_counts().to_string())


def main():
    scenarios = load_scenarios()
    booking = get_test_booking()
    print(f"Running {len(scenarios)} scenarios against booking {booking['external_id']}\n")

    orch = Orchestrator()
    run_id = uuid.uuid4().hex[:6]
    results = []
    for i, s in enumerate(scenarios, 1):
        print(f"  [{i:2d}/{len(scenarios)}] {s['id']}  {s['text'][:60]}...", flush=True)
        try:
            results.append(run_scenario(orch, s, booking, run_id))
        except Exception as e:
            print(f"    ERROR: {type(e).__name__}: {e}")
            results.append({
                "scenario_id": s["id"], "text": s["text"],
                "expected_intent": s["expected_intent"],
                "expected_risk": s["expected_risk"],
                "expected_tools": sorted(s["expected_tools_any_of"]),
                "actual_intent": "error", "actual_risk": "error", "actual_tools": [],
                "escalated": False, "processing_ms": 0.0,
                "intent_correct": False, "risk_correct": False, "tool_correct": False,
            })

    df = report(results)

    out = Path(__file__).parent / f"results_{run_id}.csv"
    df.to_csv(out, index=False)
    print(f"\nResults CSV: {out}")

    dump_from_audit_log()


if __name__ == "__main__":
    main()
