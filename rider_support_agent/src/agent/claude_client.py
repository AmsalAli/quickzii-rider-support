'''Thin Anthropic SDK wrapper for the rider support agent.

Deliberately minimal: does not know about tool execution, audit logging,
retry state, or escalation. Those responsibilities live in the
orchestrator (Batch C). This file only knows how to talk to Claude.
'''
from typing import Any
import anthropic

from src.config.settings import settings
from src.agent.system_prompt import SYSTEM_PROMPT
from src.tools.tool_definitions import TOOLS


class ClaudeClient:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def send(self, messages: list[dict[str, Any]]) -> Any:
        '''Send one turn to Claude.

        messages: full conversation history in Anthropic message format,
                  including any prior tool_use / tool_result blocks.
        Returns: the raw Anthropic Message object. The orchestrator is
                 responsible for interpreting stop_reason and content
                 blocks (text vs tool_use).
        '''
        return self._client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.agent_max_tokens,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
