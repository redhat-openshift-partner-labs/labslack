"""Handler for cluster notification API endpoint."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING

from aiohttp import web

from labslack.logging import get_logger
from labslack.metrics import get_metrics
from labslack.notifications.service import NotificationService

if TYPE_CHECKING:
    from labslack.config import Config

# Valid notification types
VALID_NOTIFICATION_TYPES = {"warning", "expiration"}


class NotifyHandler:
    """Handles POST /api/notify requests for cluster notifications."""

    def __init__(self, config: Config, notification_service: NotificationService) -> None:
        """Initialize the notify handler.

        Args:
            config: Application configuration.
            notification_service: Service for sending notifications.
        """
        self.config = config
        self.notification_service = notification_service
        self.logger = get_logger("notify_handler")
        self.metrics = get_metrics()
        self._notify_counter = self.metrics.counter(
            "notify_requests_total", "Total notification requests"
        )

    async def handle_notify(self, request: web.Request) -> web.Response:
        """Handle incoming notification POST request.

        Expected JSON body:
        {
            "cluster_id": "ocp-prod-01",
            "cluster_name": "Production Cluster",
            "owner_email": "admin@example.com",  # optional
            "expiration_date": "2024-03-15T12:00:00Z",  # optional
            "notification_type": "warning",
            "message": "Custom message"  # optional
        }
        """
        # Authenticate request
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key != self.config.webhook_api_key:
            self._notify_counter.labels(status="unauthorized").inc()
            self.logger.warning(
                "Notify request unauthorized",
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
            self._notify_counter.labels(status="invalid_json").inc()
            self.logger.warning(
                "Notify request with invalid JSON",
                extra={"remote": request.remote},
            )
            return web.json_response(
                {"error": "Invalid JSON"},
                status=400,
            )

        # Validate required fields
        validation_error = self._validate_request(data)
        if validation_error:
            self._notify_counter.labels(status="validation_error").inc()
            return web.json_response(
                {"error": validation_error},
                status=400,
            )

        # Parse optional expiration date
        expiration_date = None
        if data.get("expiration_date"):
            try:
                expiration_date = datetime.fromisoformat(
                    data["expiration_date"].replace("Z", "+00:00")
                )
            except ValueError:
                self._notify_counter.labels(status="invalid_date").inc()
                return web.json_response(
                    {"error": "Invalid expiration_date format. Use ISO 8601."},
                    status=400,
                )

        self.logger.info(
            "Processing notification request",
            extra={
                "cluster_id": data["cluster_id"],
                "notification_type": data["notification_type"],
            },
        )

        # Send the notification
        result = await self.notification_service.send_notification(
            cluster_id=data["cluster_id"],
            cluster_name=data["cluster_name"],
            notification_type=data["notification_type"],
            expiration_date=expiration_date,
            custom_message=data.get("message"),
        )

        if result.success:
            self._notify_counter.labels(status="success").inc()
            return web.json_response(
                {
                    "status": "sent",
                    "notification_id": result.notification_id,
                    "channel": result.channel,
                    "timestamp": result.timestamp,
                },
                status=200,
            )
        else:
            self._notify_counter.labels(status="send_failed").inc()
            return web.json_response(
                {
                    "status": "failed",
                    "notification_id": result.notification_id,
                    "error": result.error,
                },
                status=500,
            )

    def _validate_request(self, data: dict) -> str | None:
        """Validate the notification request data.

        Args:
            data: The parsed JSON request body.

        Returns:
            Error message string if validation fails, None if valid.
        """
        # Check required fields
        if not data.get("cluster_id"):
            return "cluster_id is required"

        if not data.get("cluster_name"):
            return "cluster_name is required"

        if not data.get("notification_type"):
            return "notification_type is required"

        # Validate notification type
        if data["notification_type"] not in VALID_NOTIFICATION_TYPES:
            return f"notification_type must be one of: {', '.join(VALID_NOTIFICATION_TYPES)}"

        return None

    def get_routes(self) -> list[web.RouteDef]:
        """Return aiohttp route definitions."""
        return [
            web.post("/api/notify", self.handle_notify),
        ]
