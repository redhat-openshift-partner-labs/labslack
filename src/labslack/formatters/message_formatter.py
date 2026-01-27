"""Message formatting with configurable metadata."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from labslack.config import Config

MAX_MESSAGE_LENGTH = 4000


class MessageFormatter:
    """Formats messages for relay with configurable metadata inclusion."""

    def __init__(self, config: Config) -> None:
        self.config = config

    def format_dm(
        self,
        text: str,
        user_id: str | None = None,
        timestamp: str | None = None,
    ) -> str:
        """Format a DM for relay."""
        if not self.config.include_metadata:
            return self._truncate(text)

        parts = []

        # Header with user mention
        if user_id:
            parts.append(f"*From:* <@{user_id}>")

        # Timestamp
        if timestamp:
            dt = self._parse_slack_timestamp(timestamp)
            if dt:
                parts.append(f"*Time:* {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # Message content
        parts.append(f"\n{text}")

        return self._truncate("\n".join(parts))

    def format_webhook(
        self,
        text: str,
        source: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """Format a webhook message for relay."""
        if not self.config.include_metadata:
            return self._truncate(text)

        parts = []

        # Source
        if source:
            parts.append(f"*Source:* {source}")

        # Additional metadata
        if metadata:
            for key, value in metadata.items():
                parts.append(f"*{key.title()}:* {value}")

        # Message content
        parts.append(f"\n{text}")

        return self._truncate("\n".join(parts))

    def _parse_slack_timestamp(self, ts: str) -> datetime | None:
        """Parse a Slack timestamp (epoch.sequence) to datetime."""
        try:
            epoch = float(ts.split(".")[0])
            return datetime.utcfromtimestamp(epoch)
        except (ValueError, IndexError):
            return None

    def _truncate(self, text: str) -> str:
        """Truncate message to Slack's limit with indicator."""
        if len(text) <= MAX_MESSAGE_LENGTH:
            return text
        return text[: MAX_MESSAGE_LENGTH - 20] + "\n\n_[Message truncated]_"
