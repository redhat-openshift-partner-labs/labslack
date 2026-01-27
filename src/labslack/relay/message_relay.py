"""Service for relaying messages to Slack channels."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slack_sdk.web.async_client import AsyncWebClient

    from labslack.config import Config
    from labslack.formatters.message_formatter import MessageFormatter


class MessageRelay:
    """Relays formatted messages to the configured Slack channel."""

    def __init__(
        self,
        config: Config,
        client: AsyncWebClient,
        formatter: MessageFormatter,
    ) -> None:
        self.config = config
        self.client = client
        self.formatter = formatter

    async def relay_dm(
        self,
        text: str,
        user_id: str | None = None,
        timestamp: str | None = None,
    ) -> None:
        """Relay a direct message to the configured channel."""
        formatted = self.formatter.format_dm(
            text=text,
            user_id=user_id,
            timestamp=timestamp,
        )
        await self._send_message(formatted)

    async def relay_webhook(
        self,
        text: str,
        source: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Relay a webhook message to the configured channel."""
        formatted = self.formatter.format_webhook(
            text=text,
            source=source,
            metadata=metadata,
        )
        await self._send_message(formatted)

    async def _send_message(self, text: str) -> None:
        """Send a message to the relay channel."""
        await self.client.chat_postMessage(
            channel=self.config.relay_channel_id,
            text=text,
        )
