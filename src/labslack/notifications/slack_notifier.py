"""Slack notifier for sending cluster notifications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from labslack.logging import get_logger

if TYPE_CHECKING:
    from slack_sdk.web.async_client import AsyncWebClient

    from labslack.config import Config


@dataclass
class SlackNotifyResult:
    """Result of a Slack notification attempt."""

    success: bool
    channel: str | None = None
    ts: str | None = None
    error: str | None = None


class SlackNotifier:
    """Sends notifications to Slack with user group mentions."""

    def __init__(self, config: Config, client: AsyncWebClient) -> None:
        """Initialize the Slack notifier.

        Args:
            config: Application configuration.
            client: Async Slack WebClient.
        """
        self.config = config
        self.client = client
        self.logger = get_logger("slack_notifier")
        self._usergroup_id: str | None = None

    async def send_notification(self, message: str) -> SlackNotifyResult:
        """Send a notification to the configured channel with @opladmins mention.

        Args:
            message: The formatted message to send.

        Returns:
            SlackNotifyResult with success status and message details.
        """
        channel_id = self.config.notifications_channel_id
        if not channel_id:
            self.logger.error("NOTIFICATIONS_CHANNEL_ID not configured")
            return SlackNotifyResult(
                success=False,
                error="NOTIFICATIONS_CHANNEL_ID not configured",
            )

        # Build message with user group mention
        mention = await self._get_usergroup_mention()
        full_message = f"{mention}\n\n{message}" if mention else message

        try:
            response = await self.client.chat_postMessage(
                channel=channel_id,
                text=full_message,
                mrkdwn=True,
            )

            self.logger.info(
                "Notification sent to Slack",
                extra={"channel": channel_id, "ts": response.get("ts")},
            )

            return SlackNotifyResult(
                success=True,
                channel=channel_id,
                ts=response.get("ts"),
            )

        except Exception as e:
            error_msg = str(e)
            self.logger.error(
                "Failed to send Slack notification",
                extra={"channel": channel_id, "error": error_msg},
            )
            return SlackNotifyResult(
                success=False,
                channel=channel_id,
                error=error_msg,
            )

    async def _get_usergroup_mention(self) -> str | None:
        """Get the user group mention string.

        Returns the Slack mention format for user groups: <!subteam^ID|@handle>
        """
        group_handle = self.config.opladmins_group_handle
        if not group_handle:
            return None

        # If we already have the ID, use it
        if self._usergroup_id:
            return f"<!subteam^{self._usergroup_id}|@{group_handle}>"

        # Try to look up the user group ID
        try:
            response = await self.client.usergroups_list()
            if response.get("ok"):
                for group in response.get("usergroups", []):
                    if group.get("handle") == group_handle:
                        self._usergroup_id = group.get("id")
                        return f"<!subteam^{self._usergroup_id}|@{group_handle}>"

            # User group not found, fall back to just mentioning by handle
            self.logger.warning(
                "User group not found, using handle only",
                extra={"handle": group_handle},
            )
            return f"@{group_handle}"

        except Exception as e:
            self.logger.warning(
                "Failed to lookup user group, using handle only",
                extra={"handle": group_handle, "error": str(e)},
            )
            return f"@{group_handle}"
