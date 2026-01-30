"""Message formatters for cluster notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

NotificationType = Literal["warning", "expiration"]


class NotificationFormatter:
    """Formats cluster notification messages for Slack."""

    def format_message(
        self,
        cluster_id: str,
        cluster_name: str,
        notification_type: NotificationType,
        expiration_date: datetime | None = None,
        custom_message: str | None = None,
    ) -> str:
        """Format a notification message.

        Args:
            cluster_id: Unique cluster identifier.
            cluster_name: Human-readable cluster name.
            notification_type: Either "warning" or "expiration".
            expiration_date: Optional expiration timestamp.
            custom_message: Optional custom message to use instead of generated.

        Returns:
            Formatted message string for Slack.
        """
        if custom_message:
            return self._format_with_custom_message(
                cluster_id, cluster_name, custom_message
            )

        if notification_type == "warning":
            return self._format_warning(cluster_id, cluster_name, expiration_date)
        return self._format_expiration(cluster_id, cluster_name)

    def _format_with_custom_message(
        self,
        cluster_id: str,
        cluster_name: str,
        message: str,
    ) -> str:
        """Format a notification with a custom message."""
        return (
            f":warning: *Cluster Notification*\n\n"
            f"*Cluster:* {cluster_name} (`{cluster_id}`)\n\n"
            f"{message}"
        )

    def _format_warning(
        self,
        cluster_id: str,
        cluster_name: str,
        expiration_date: datetime | None,
    ) -> str:
        """Format a 48-hour warning message."""
        time_info = ""
        if expiration_date:
            formatted_date = expiration_date.strftime("%Y-%m-%d %H:%M UTC")
            time_info = f"\n*Expires:* {formatted_date}"

        return (
            f":warning: *Cluster Expiration Warning*\n\n"
            f"*Cluster:* {cluster_name} (`{cluster_id}`){time_info}\n\n"
            f"This cluster will expire in approximately *48 hours*. "
            f"Please take action to extend or decommission."
        )

    def _format_expiration(
        self,
        cluster_id: str,
        cluster_name: str,
    ) -> str:
        """Format an expiration notification."""
        return (
            f":rotating_light: *Cluster Expired*\n\n"
            f"*Cluster:* {cluster_name} (`{cluster_id}`)\n\n"
            f"This cluster has reached its expiration date and will be decommissioned."
        )
