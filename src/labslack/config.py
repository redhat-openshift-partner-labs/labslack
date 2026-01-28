"""Configuration management for LabSlack bot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from environment variables."""

    slack_bot_token: str
    slack_signing_secret: str
    relay_channel_id: str | None = None  # Optional for initial URL verification
    include_metadata: bool = True
    webhook_api_key: str | None = None
    host: str = "0.0.0.0"
    port: int = 3000
    log_level: str = "INFO"
    max_retries: int = 3
    retry_base_delay: float = 1.0

    @classmethod
    def from_env(cls) -> Self:
        """Load configuration from environment variables."""
        return cls(
            slack_bot_token=os.environ["SLACK_BOT_TOKEN"],
            slack_signing_secret=os.environ["SLACK_SIGNING_SECRET"],
            relay_channel_id=os.getenv("RELAY_CHANNEL_ID"),  # Now optional
            include_metadata=os.getenv("INCLUDE_METADATA", "true").lower() == "true",
            webhook_api_key=os.getenv("WEBHOOK_API_KEY"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "3000")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            retry_base_delay=float(os.getenv("RETRY_BASE_DELAY", "1.0")),
        )
