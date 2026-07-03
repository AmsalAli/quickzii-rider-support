'''Central configuration for the rider support agent.

Loaded from .env. Fails loudly at startup on missing keys.
Timing mode (production vs demo) is the mechanism your Methodology chapter
will reference: production timings preserved for deployment realism, demo
timings shortened for viva demonstration.
'''
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # Claude API
    anthropic_api_key: str
    claude_model: str = 'claude-sonnet-4-6'
    agent_max_tokens: int = 1024

    # Mock MotionTools connection
    motiontools_base_url: str = 'http://127.0.0.1:8001'

    # Timing mode
    timing_mode: Literal['production', 'demo'] = 'demo'
    demo_retry_seconds_order_not_in_resto: int = 30
    demo_retry_seconds_order_not_ready: int = 45
    prod_retry_seconds_order_not_in_resto: int = 300
    prod_retry_seconds_order_not_ready: int = 600

    # Audit
    audit_log_path: str = 'data/logs/action_log.jsonl'

    # Safety
    max_tool_call_rounds: int = 5

    # Server
    host: str = '127.0.0.1'
    port: int = 8002

    # ---------- Derived timing helpers ----------

    @property
    def retry_seconds_order_not_in_resto(self) -> int:
        return (self.prod_retry_seconds_order_not_in_resto
                if self.timing_mode == 'production'
                else self.demo_retry_seconds_order_not_in_resto)

    @property
    def retry_seconds_order_not_ready(self) -> int:
        return (self.prod_retry_seconds_order_not_ready
                if self.timing_mode == 'production'
                else self.demo_retry_seconds_order_not_ready)


settings = Settings()
