"""Handler for external webhook messages."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from labslack.config import Config
    from labslack.relay.message_relay import MessageRelay


class WebhookHandler:
    """Handles incoming webhook requests and relays messages."""

    def __init__(self, config: Config, relay: MessageRelay) -> None:
        self.config = config
        self.relay = relay

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming webhook POST request."""
        # Authenticate request
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != self.config.webhook_api_key:
            return web.json_response(
                {"error": "Unauthorized"},
                status=401,
            )

        # Parse JSON body
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"error": "Invalid JSON"},
                status=400,
            )

        # Validate required fields
        message = data.get("message")
        if message is None:
            return web.json_response(
                {"error": "Missing required field: message"},
                status=400,
            )

        if not message.strip():
            return web.json_response(
                {"error": "Message cannot be empty"},
                status=400,
            )

        # Extract optional fields
        source = data.get("source")
        metadata = {k: v for k, v in data.items() if k not in ("message", "source")}

        # Relay the message
        await self.relay.relay_webhook(
            text=message,
            source=source,
            metadata=metadata,
        )

        return web.json_response({"status": "ok"})

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({"status": "healthy"})

    def get_routes(self) -> list[web.RouteDef]:
        """Return aiohttp route definitions."""
        return [
            web.post("/webhook", self.handle_webhook),
            web.get("/health", self.health_check),
        ]
