"""Unit tests for notification service."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from labslack.config import Config
from labslack.database.models import NotificationStatus
from labslack.notifications.service import NotificationService
from labslack.notifications.slack_notifier import SlackNotifyResult


@pytest.fixture
def config_with_notifications() -> Config:
    """Create a test config with notification settings."""
    return Config(
        slack_bot_token="xoxb-test-token",
        slack_signing_secret="test-signing-secret",
        relay_channel_id="C0123456789",
        webhook_api_key="test-api-key-123",
        notifications_channel_id="C9876543210",
        opladmins_group_handle="opladmins",
        database_path=":memory:",
    )


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock Slack async client."""
    client = MagicMock()
    client.chat_postMessage = AsyncMock(
        return_value={"ok": True, "ts": "1234567890.123456"}
    )
    client.usergroups_list = AsyncMock(
        return_value={
            "ok": True,
            "usergroups": [{"id": "S12345678", "handle": "opladmins"}],
        }
    )
    return client


@pytest.fixture
def service(config_with_notifications: Config, mock_client: MagicMock) -> NotificationService:
    """Create a NotificationService instance."""
    return NotificationService(config_with_notifications, mock_client)


class TestSendNotification:
    """Tests for sending notifications."""

    @pytest.mark.asyncio
    async def test_send_notification_success(
        self, service: NotificationService
    ) -> None:
        """Test successful notification sending."""
        with patch(
            "labslack.notifications.service.save_notification", new_callable=AsyncMock
        ):
            result = await service.send_notification(
                cluster_id="ocp-prod-01",
                cluster_name="Production Cluster",
                notification_type="warning",
            )

        assert result.success is True
        assert result.notification_id is not None
        assert result.channel == "C9876543210"

    @pytest.mark.asyncio
    async def test_send_notification_with_expiration(
        self, service: NotificationService
    ) -> None:
        """Test notification with expiration date."""
        expiration = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

        with patch(
            "labslack.notifications.service.save_notification", new_callable=AsyncMock
        ):
            result = await service.send_notification(
                cluster_id="ocp-prod-01",
                cluster_name="Production Cluster",
                notification_type="warning",
                expiration_date=expiration,
            )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_notification_with_custom_message(
        self, service: NotificationService
    ) -> None:
        """Test notification with custom message."""
        with patch(
            "labslack.notifications.service.save_notification", new_callable=AsyncMock
        ):
            result = await service.send_notification(
                cluster_id="ocp-prod-01",
                cluster_name="Production Cluster",
                notification_type="warning",
                custom_message="Custom alert text",
            )

        assert result.success is True


class TestHistoryRecording:
    """Tests for notification history recording."""

    @pytest.mark.asyncio
    async def test_successful_notification_recorded(
        self, service: NotificationService
    ) -> None:
        """Test that successful notification is recorded in history."""
        save_mock = AsyncMock()
        with patch(
            "labslack.notifications.service.save_notification", save_mock
        ):
            await service.send_notification(
                cluster_id="ocp-prod-01",
                cluster_name="Production Cluster",
                notification_type="warning",
            )

        save_mock.assert_called_once()
        saved_notification = save_mock.call_args[0][0]
        assert saved_notification.cluster_id == "ocp-prod-01"
        assert saved_notification.status == NotificationStatus.SENT

    @pytest.mark.asyncio
    async def test_failed_notification_recorded_with_error(
        self, config_with_notifications: Config, mock_client: MagicMock
    ) -> None:
        """Test that failed notification is recorded with error message."""
        mock_client.chat_postMessage = AsyncMock(
            side_effect=Exception("Slack API error")
        )
        service = NotificationService(config_with_notifications, mock_client)

        save_mock = AsyncMock()
        with patch(
            "labslack.notifications.service.save_notification", save_mock
        ):
            result = await service.send_notification(
                cluster_id="ocp-prod-01",
                cluster_name="Production Cluster",
                notification_type="warning",
            )

        assert result.success is False
        save_mock.assert_called_once()
        saved_notification = save_mock.call_args[0][0]
        assert saved_notification.status == NotificationStatus.FAILED
        assert saved_notification.error_message == "Slack API error"

    @pytest.mark.asyncio
    async def test_history_save_failure_does_not_fail_request(
        self, service: NotificationService
    ) -> None:
        """Test that history save failure doesn't fail the notification."""
        with patch(
            "labslack.notifications.service.save_notification",
            AsyncMock(side_effect=Exception("DB error")),
        ):
            result = await service.send_notification(
                cluster_id="ocp-prod-01",
                cluster_name="Production Cluster",
                notification_type="warning",
            )

        # Notification should still succeed
        assert result.success is True
