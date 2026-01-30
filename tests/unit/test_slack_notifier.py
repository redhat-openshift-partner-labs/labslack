"""Unit tests for Slack notifier."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from labslack.config import Config
from labslack.notifications.slack_notifier import SlackNotifier, SlackNotifyResult


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
            "usergroups": [
                {"id": "S12345678", "handle": "opladmins"},
            ],
        }
    )
    return client


@pytest.fixture
def notifier(config_with_notifications: Config, mock_client: MagicMock) -> SlackNotifier:
    """Create a SlackNotifier instance."""
    return SlackNotifier(config_with_notifications, mock_client)


class TestSendNotification:
    """Tests for sending notifications."""

    @pytest.mark.asyncio
    async def test_send_notification_success(
        self, notifier: SlackNotifier, mock_client: MagicMock
    ) -> None:
        """Test successful notification sending."""
        result = await notifier.send_notification("Test message")

        assert result.success is True
        assert result.channel == "C9876543210"
        assert result.ts == "1234567890.123456"
        assert result.error is None

        mock_client.chat_postMessage.assert_called_once()
        call_kwargs = mock_client.chat_postMessage.call_args.kwargs
        assert call_kwargs["channel"] == "C9876543210"
        assert "Test message" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_send_notification_with_usergroup_mention(
        self, notifier: SlackNotifier, mock_client: MagicMock
    ) -> None:
        """Test that notification includes user group mention."""
        await notifier.send_notification("Test message")

        call_kwargs = mock_client.chat_postMessage.call_args.kwargs
        # Should contain the subteam mention format
        assert "<!subteam^S12345678|@opladmins>" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_send_notification_slack_error(
        self, notifier: SlackNotifier, mock_client: MagicMock
    ) -> None:
        """Test notification failure handling."""
        mock_client.chat_postMessage = AsyncMock(
            side_effect=Exception("Slack API error")
        )

        result = await notifier.send_notification("Test message")

        assert result.success is False
        assert result.error == "Slack API error"


class TestMissingConfiguration:
    """Tests for missing configuration handling."""

    @pytest.mark.asyncio
    async def test_missing_channel_returns_error(self, mock_client: MagicMock) -> None:
        """Test that missing channel ID returns error."""
        config = Config(
            slack_bot_token="xoxb-test",
            slack_signing_secret="test-secret",
            notifications_channel_id=None,  # Missing
        )
        notifier = SlackNotifier(config, mock_client)

        result = await notifier.send_notification("Test")

        assert result.success is False
        assert "not configured" in result.error.lower()


class TestUserGroupLookup:
    """Tests for user group lookup."""

    @pytest.mark.asyncio
    async def test_usergroup_not_found_falls_back(
        self, config_with_notifications: Config, mock_client: MagicMock
    ) -> None:
        """Test fallback when user group not found."""
        mock_client.usergroups_list = AsyncMock(
            return_value={"ok": True, "usergroups": []}
        )
        notifier = SlackNotifier(config_with_notifications, mock_client)

        await notifier.send_notification("Test message")

        call_kwargs = mock_client.chat_postMessage.call_args.kwargs
        # Should fall back to @handle format
        assert "@opladmins" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_usergroup_lookup_error_falls_back(
        self, config_with_notifications: Config, mock_client: MagicMock
    ) -> None:
        """Test fallback when user group lookup fails."""
        mock_client.usergroups_list = AsyncMock(
            side_effect=Exception("API error")
        )
        notifier = SlackNotifier(config_with_notifications, mock_client)

        result = await notifier.send_notification("Test message")

        # Should still succeed with fallback mention
        assert result.success is True

    @pytest.mark.asyncio
    async def test_usergroup_id_cached(
        self, notifier: SlackNotifier, mock_client: MagicMock
    ) -> None:
        """Test that user group ID is cached after lookup."""
        await notifier.send_notification("First message")
        await notifier.send_notification("Second message")

        # usergroups_list should only be called once
        assert mock_client.usergroups_list.call_count == 1
