"""Notification service orchestrating formatting, sending, and history storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from labslack.database.connection import save_notification
from labslack.database.models import NotificationHistory, NotificationStatus
from labslack.logging import get_logger
from labslack.notifications.formatters import NotificationFormatter, NotificationType
from labslack.notifications.slack_notifier import SlackNotifier

if TYPE_CHECKING:
    from slack_sdk.web.async_client import AsyncWebClient

    from labslack.config import Config


@dataclass
class NotificationResult:
    """Result of a notification request."""

    success: bool
    notification_id: str
    channel: str | None = None
    timestamp: str | None = None
    error: str | None = None


class NotificationService:
    """Orchestrates cluster notifications: format -> send -> store."""

    def __init__(self, config: Config, client: AsyncWebClient) -> None:
        """Initialize the notification service.

        Args:
            config: Application configuration.
            client: Async Slack WebClient.
        """
        self.config = config
        self.formatter = NotificationFormatter()
        self.notifier = SlackNotifier(config, client)
        self.logger = get_logger("notification_service")

    async def send_notification(
        self,
        cluster_id: str,
        cluster_name: str,
        notification_type: NotificationType,
        expiration_date: datetime | None = None,
        custom_message: str | None = None,
    ) -> NotificationResult:
        """Send a cluster notification and record in history.

        Args:
            cluster_id: Unique cluster identifier.
            cluster_name: Human-readable cluster name.
            notification_type: Either "warning" or "expiration".
            expiration_date: Optional expiration timestamp.
            custom_message: Optional custom message.

        Returns:
            NotificationResult with success status and details.
        """
        # Format the message
        message = self.formatter.format_message(
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            notification_type=notification_type,
            expiration_date=expiration_date,
            custom_message=custom_message,
        )

        self.logger.info(
            "Sending cluster notification",
            extra={
                "cluster_id": cluster_id,
                "notification_type": notification_type,
            },
        )

        # Send to Slack
        slack_result = await self.notifier.send_notification(message)

        # Create history record
        if slack_result.success:
            status = NotificationStatus.SENT
            error_message = None
        else:
            status = NotificationStatus.FAILED
            error_message = slack_result.error

        history = NotificationHistory.create(
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            notification_type=notification_type,
            message=message,
            status=status,
            error_message=error_message,
            slack_channel=slack_result.channel,
            slack_ts=slack_result.ts,
        )

        # Save to database
        try:
            await save_notification(history)
            self.logger.info(
                "Notification recorded in history",
                extra={"notification_id": history.id, "status": status.value},
            )
        except Exception as e:
            self.logger.error(
                "Failed to save notification history",
                extra={"notification_id": history.id, "error": str(e)},
            )
            # Don't fail the request if history save fails

        return NotificationResult(
            success=slack_result.success,
            notification_id=history.id,
            channel=slack_result.channel,
            timestamp=history.created_at.isoformat(),
            error=slack_result.error,
        )
