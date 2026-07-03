# Quickzii - Human-in-the-Loop AI Rider Support Agent

**MSc Artificial Intelligence Dissertation**
Berlin School of Business and Innovation (BSBI) / University for the Creative Arts (UCA)
Author: Hafiz Amsal Ali
Supervisor: Professor Vincent English

---

## Overview

This repository contains the complete prototype for a dissertation on human-in-the-loop AI conversational agents for automating rider support in food-delivery logistics. The system is inspired by the manual Intercom + MotionTools workflow used by dispatchers in real logistics operations, and demonstrates how a large language model agent, given the right tools and escalation policy, can automate the routine 60-90% of rider queries while routing genuinely risky cases to a human reviewer.

The full system is deployed and clickable. The link and access instructions are below.

---

## Live Demonstration

**Primary URL (production frontend):** https://quickzii-rider-support-eta.vercel.app

**Backend services** (called by the frontend, publicly accessible for API inspection):

- Mock MotionTools API (FastAPI + SQLite): https://mock-motiontools.onrender.com
  - Interactive documentation: https://mock-motiontools.onrender.com/docs
- Rider Support Agent (FastAPI + Anthropic Claude API): https://rider-support-agent.onrender.com
  - Health check: https://rider-support-agent.onrender.com/health

### Access pages

Once loaded, four pages are reachable from the main URL:

| Page | Purpose |
|---|---|
| `/` | Rider Chat Interface (start here) |
| `/bookings` | Booking Detail Page (mock MotionTools) |
| `/drivers` | Driver Detail Page (mock MotionTools) |
| `/dashboard` | Human Agent Dashboard (escalation queues and audit log) |

### Important: cold-start behaviour

Both backend services are deployed on Render free tier. This is a deliberate deployment choice, documented in the Methodology chapter, and it has one visible consequence for the reviewer:

**If the services have not been used for 15 minutes, the first request will take 30-60 seconds while the services warm up.** All subsequent requests are fast. This is expected free-tier behaviour, not a system failure.

**Recommended first-visit sequence:**

1. Open the primary URL in a browser
2. If the greeting message does not appear within 15 seconds, wait, the frontend is warming up
3. Click any quick-reply button (for example, *I cannot reach out to the customer*)
4. First message may take up to 60 seconds (cold start on both services plus LLM round-trip)
5. Subsequent messages respond in 5-10 seconds

---

## Recommended Test Scenarios

To exercise the three risk tiers documented in the dissertation, please try:

**Low-risk (autonomous):**
- Press *I cannot reach out to the customer*, the AI should look up the booking and share the customer contact details automatically
- Press *Order is not ready yet*, the AI should ask the rider to wait ten minutes and log a wait timer against the booking

**Medium-risk (human review):**
- Press *Vehicle breakdown* and describe a short scenario (for example: *bike chain snapped, one kilometre from drop-off*)
- The AI should prepare a proposed reply and queue the case for human review, visible on the `/dashboard` page under the Medium Queue tab

**High-risk (escalation):**
- Press *Order is damaged* and briefly describe the situation
- The AI should ask one clarifying question and then escalate, visible on `/dashboard` under the High Queue tab

The Audit Log tab on the dashboard reflects every rider message, tool call, escalation, and human action in real time.

---

## Architecture in Brief

Rider -> Frontend (Next.js on Vercel) -> Agent (FastAPI on Render) -> Claude API (tool-use loop) -> Mock MotionTools (FastAPI on Render) -> SQLite

The agent classifies rider intent, applies a deterministic risk-tier lookup, and either resolves the request autonomously (low-risk), proposes a reply for human approval (medium-risk), or escalates for full human handling (high-risk). Every step is written to an append-only audit log which is the row-level data source for the Findings chapter.

Design decisions (each defended in the Methodology chapter):
- Transparent custom orchestrator, no LangChain or LangGraph, in the interest of auditability
- Deterministic intent-to-risk lookup rather than LLM-driven risk assessment
- SQLite rather than PostgreSQL, appropriate for prototype scale
- Anonymisation of real driver PII at data ingest for GDPR compliance
- Dual-mode timing (production 5/10 minute retry timers; demo mode with shortened intervals for viva demonstration)

---

## Evaluation Results

The evaluation harness in `rider_support_agent/evaluation/` runs a set of 15 labelled scenarios covering all nine intents and all three risk tiers. Results across two runs (single-turn and multi-turn):

| Metric | Value |
|---|---|
| Intent classification accuracy | 86.7% |
| Risk-tier accuracy | 86.7% |
| First-turn action rate (single-turn) | 60.0% |
| Full-flow tool-call correctness (multi-turn) | 86.7% |
| LOW-risk automation rate | 100% |
| MEDIUM-risk escalation rate | 60% |
| HIGH-risk escalation rate | 100% |
| Median processing time (multi-turn) | 9.2 seconds |

The gap between the first-turn action rate and the full-flow correctness reflects intentional safety behaviour: for order damage, customer refusal, and app-completion scenarios, the agent asks a clarifying question before acting. Complete numbers, per-scenario detail, and confusion matrix are in `rider_support_agent/evaluation/results_multiturn_e485e2.csv`.

---

## Running Locally

Full local setup is documented in the `LOCAL_SETUP.md` file. Briefly:

1. Clone this repository
2. In `mock_motiontools/`: create a Python venv, install requirements, run `python scripts/seed.py` then `python run.py`
3. In `rider_support_agent/`: create a venv, install requirements, create `.env` with `ANTHROPIC_API_KEY`, then `python run.py`
4. In `quickzii_app/`: `pnpm install`, then `pnpm dev`

The system runs at `http://localhost:3000`.

---

## Limitations

- The MotionTools API is a functional clone, not the real dispatch system. Real API access was requested through the researcher employer but was not granted within the project timeline, so the prototype was evaluated against a faithful mock. This is discussed in the Methodology chapter of the dissertation.
- Free-tier deployment introduces cold-start latency of 30-60 seconds after periods of inactivity.
- Escalation queue is held in memory in the prototype. Production would use a persistent queue.
- The 60% first-turn action rate is a designed safety trade-off, not a defect: the agent deliberately asks a clarifying question before acting on ambiguous high-risk reports.

---

## Contact

Hafiz Amsal Ali
BSBI / UCA MSc Artificial Intelligence