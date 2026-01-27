"""Handler for direct messages to the bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slack_bolt import App

    from labslack.config import Config
    from labslack.relay.message_relay import MessageRelay


class DMHandler:
    """Handles direct messages sent to the bot and relays them."""

    def __init__(self, config: Config, relay: MessageRelay) -> None:
        self.config = config
        self.relay = relay

    def register(self, app: App) -> None:
        """Register the DM event handler with the Bolt app."""

        @app.event("message")
        def handle_message(event: dict, say: callable, client: object) -> None:
            # Skip bot messages and message subtypes
            if event.get("bot_id") or event.get("subtype"):
                return

            # Only handle DMs (channel_type == "im")
            if event.get("channel_type") != "im":
                return

            text = event.get("text", "").strip()
            if not text:
                return

            user_id = event.get("user")
            timestamp = event.get("ts")

            self.relay.relay_dm(
                text=text,
                user_id=user_id,
                timestamp=timestamp,
            )
