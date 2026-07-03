"""Checkpoint for Batch B of the agent build.

Sends three hand-crafted rider messages representing LOW, MEDIUM, and
HIGH risk intents and prints Claudes response so we can confirm:
  - the system prompt loads
  - Claude reaches the right conversational move for each
  - Claude produces well-formed tool_use blocks

NO tool execution happens here. This is a dry run of the reasoning layer.
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agent.claude_client import ClaudeClient


SCENARIOS = [
    {
        "label": "LOW-risk: customer unreachable (rider clearly wants contact)",
        "user_message": (
            "I pressed 'I cannot reach out to the customer' -- they are not "
            "picking up. Booking BK-external-XXXXXX."
        ),
    },
    {
        "label": "MEDIUM-risk: vehicle breakdown",
        "user_message": (
            "I pressed 'Vehicle breakdown'. My bike chain snapped, I am about "
            "1km from the drop-off. Not sure what to do."
        ),
    },
    {
        "label": "HIGH-risk: order damaged",
        "user_message": (
            "I pressed 'Order is damaged'. When I picked it up from the "
            "restaurant the box was already crushed and there is sauce leaking."
        ),
    },
]


def summarize_block(block) -> str:
    btype = getattr(block, "type", "unknown")
    if btype == "text":
        text = getattr(block, "text", "")
        return f"    TEXT: {text.strip()}"
    if btype == "tool_use":
        name = getattr(block, "name", "?")
        inp = getattr(block, "input", {})
        return f"    TOOL_USE: {name}({json.dumps(inp, indent=2, ensure_ascii=False)})"
    return f"    {btype}: {block!r}"


def main():
    client = ClaudeClient()

    for i, scenario in enumerate(SCENARIOS, 1):
        print("=" * 70)
        print(f"Scenario {i}: {scenario['label']}")
        print(f"Rider says: {scenario['user_message']!r}")
        print("-" * 70)

        response = client.send(messages=[
            {"role": "user", "content": scenario["user_message"]},
        ])

        print(f"stop_reason: {response.stop_reason}")
        print("content blocks:")
        for block in response.content:
            print(summarize_block(block))
        print()

    print("Batch B checkpoint complete.")
    print("Review each scenario: did Claude produce sensible tool calls / text?")


if __name__ == "__main__":
    main()
