"""Handler for external webhook messages."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from aiohttp import web

from labslack.logging import get_logger
from labslack.metrics import get_metrics

if TYPE_CHECKING:
    from labslack.config import Config
    from labslack.relay.message_relay import MessageRelay


class WebhookHandler:
    """Handles incoming webhook requests and relays messages."""

    def __init__(self, config: Config, relay: MessageRelay) -> None:
        self.config = config
        self.relay = relay
        self.logger = get_logger("webhook_handler")
        self.metrics = get_metrics()
        self._webhook_counter = self.metrics.counter(
            "webhook_requests_total", "Total webhook requests"
        )
        self._relay_latency = self.metrics.histogram(
            "relay_latency_seconds", "Relay operation latency"
        )

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming webhook POST request."""
        # Authenticate request
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != self.config.webhook_api_key:
            self._webhook_counter.labels(status="unauthorized").inc()
            self.logger.warning(
                "Webhook request unauthorized",
                extra={"remote": request.remote},
            )
            return web.json_response(
                {"error": "Unauthorized"},
                status=401,
            )

        # Parse JSON body
        try:
            data = await request.json()
        except json.JSONDecodeError:
            self._webhook_counter.labels(status="invalid_json").inc()
            self.logger.warning(
                "Webhook request with invalid JSON",
                extra={"remote": request.remote},
            )
            return web.json_response(
                {"error": "Invalid JSON"},
                status=400,
            )

        # Validate required fields
        message = data.get("message")
        if message is None:
            self._webhook_counter.labels(status="missing_message").inc()
            return web.json_response(
                {"error": "Missing required field: message"},
                status=400,
            )

        if not message.strip():
            self._webhook_counter.labels(status="empty_message").inc()
            return web.json_response(
                {"error": "Message cannot be empty"},
                status=400,
            )

        # Extract optional fields
        source = data.get("source")
        metadata = {k: v for k, v in data.items() if k not in ("message", "source")}

        self.logger.info(
            "Processing webhook request",
            extra={"source": source, "message_length": len(message)},
        )

        # Relay the message with timing
        with self._relay_latency.labels(source="webhook").time():
            success = await self.relay.relay_webhook(
                text=message,
                source=source,
                metadata=metadata,
            )

        if success:
            self._webhook_counter.labels(status="success").inc()
        else:
            self._webhook_counter.labels(status="relay_failed").inc()

        return web.json_response({"status": "ok"})

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        return web.json_response({"status": "healthy"})

    async def metrics_endpoint(self, request: web.Request) -> web.Response:
        """Metrics endpoint for observability."""
        all_metrics = self.metrics.get_all()
        return web.json_response(all_metrics)

    def get_routes(self) -> list[web.RouteDef]:
        """Return aiohttp route definitions."""
        return [
            web.post("/webhook", self.handle_webhook),
            web.get("/health", self.health_check),
            web.get("/metrics", self.metrics_endpoint),
        ]
