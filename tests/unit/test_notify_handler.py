"""Unit tests for NotifyHandler."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from labslack.config import Config
from labslack.handlers.notify_handler import NotifyHandler
from labslack.notifications.service import NotificationResult


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
def mock_notification_service() -> MagicMock:
    """Create a mock NotificationService."""
    service = MagicMock()
    service.send_notification = AsyncMock(
        return_value=NotificationResult(
            success=True,
            notification_id="test-uuid-123",
            channel="C9876543210",
            timestamp="2024-03-13T12:00:00",
        )
    )
    return service


@pytest.fixture
def handler(
    config_with_notifications: Config, mock_notification_service: MagicMock
) -> NotifyHandler:
    """Create a NotifyHandler instance."""
    return NotifyHandler(config_with_notifications, mock_notification_service)


class TestNotifyAuthentication:
    """Tests for notify endpoint authentication."""

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_401(self, handler: NotifyHandler) -> None:
        """Test that missing API key returns 401."""
        request = MagicMock()
        request.headers = {}
        request.remote = "127.0.0.1"

        response = await handler.handle_notify(request)

        assert response.status == 401
        body = json.loads(response.body)
        assert body["error"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_401(self, handler: NotifyHandler) -> None:
        """Test that invalid API key returns 401."""
        request = MagicMock()
        request.headers = {"X-API-Key": "wrong-key"}
        request.remote = "127.0.0.1"

        response = await handler.handle_notify(request)

        assert response.status == 401

    @pytest.mark.asyncio
    async def test_valid_api_key_succeeds(
        self, handler: NotifyHandler, mock_notification_service: MagicMock
    ) -> None:
        """Test that valid API key allows request."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.remote = "127.0.0.1"
        request.json = AsyncMock(
            return_value={
                "cluster_id": "ocp-prod-01",
                "cluster_name": "Production Cluster",
                "notification_type": "warning",
            }
        )

        response = await handler.handle_notify(request)

        assert response.status == 200


class TestNotifyValidation:
    """Tests for notify endpoint request validation."""

    @pytest.mark.asyncio
    async def test_missing_cluster_id_returns_400(self, handler: NotifyHandler) -> None:
        """Test that missing cluster_id returns 400."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.remote = "127.0.0.1"
        request.json = AsyncMock(
            return_value={
                "cluster_name": "Production",
                "notification_type": "warning",
            }
        )

        response = await handler.handle_notify(request)

        assert response.status == 400
        body = json.loads(response.body)
        assert "cluster_id" in body["error"]

    @pytest.mark.asyncio
    async def test_missing_cluster_name_returns_400(
        self, handler: NotifyHandler
    ) -> None:
        """Test that missing cluster_name returns 400."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.remote = "127.0.0.1"
        request.json = AsyncMock(
            return_value={
                "cluster_id": "ocp-prod-01",
                "notification_type": "warning",
            }
        )

        response = await handler.handle_notify(request)

        assert response.status == 400
        body = json.loads(response.body)
        assert "cluster_name" in body["error"]

    @pytest.mark.asyncio
    async def test_missing_notification_type_returns_400(
        self, handler: NotifyHandler
    ) -> None:
        """Test that missing notification_type returns 400."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.remote = "127.0.0.1"
        request.json = AsyncMock(
            return_value={
                "cluster_id": "ocp-prod-01",
                "cluster_name": "Production Cluster",
            }
        )

        response = await handler.handle_notify(request)

        assert response.status == 400
        body = json.loads(response.body)
        assert "notification_type" in body["error"]

    @pytest.mark.asyncio
    async def test_invalid_notification_type_returns_400(
        self, handler: NotifyHandler
    ) -> None:
        """Test that invalid notification_type returns 400."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.remote = "127.0.0.1"
        request.json = AsyncMock(
            return_value={
                "cluster_id": "ocp-prod-01",
                "cluster_name": "Production Cluster",
                "notification_type": "invalid",
            }
        )

        response = await handler.handle_notify(request)

        assert response.status == 400
        body = json.loads(response.body)
        assert "notification_type" in body["error"]

    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(self, handler: NotifyHandler) -> None:
        """Test that invalid JSON returns 400."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.remote = "127.0.0.1"
        request.json = AsyncMock(side_effect=json.JSONDecodeError("", "", 0))

        response = await handler.handle_notify(request)

        assert response.status == 400
        body = json.loads(response.body)
        assert "json" in body["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_expiration_date_returns_400(
        self, handler: NotifyHandler
    ) -> None:
        """Test that invalid expiration_date format returns 400."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.remote = "127.0.0.1"
        request.json = AsyncMock(
            return_value={
                "cluster_id": "ocp-prod-01",
                "cluster_name": "Production Cluster",
                "notification_type": "warning",
                "expiration_date": "not-a-date",
            }
        )

        response = await handler.handle_notify(request)

        assert response.status == 400
        body = json.loads(response.body)
        assert "expiration_date" in body["error"]


class TestNotifySuccess:
    """Tests for successful notify requests."""

    @pytest.mark.asyncio
    async def test_successful_notification_returns_200(
        self, handler: NotifyHandler, mock_notification_service: MagicMock
    ) -> None:
        """Test that successful notification returns 200."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.remote = "127.0.0.1"
        request.json = AsyncMock(
            return_value={
                "cluster_id": "ocp-prod-01",
                "cluster_name": "Production Cluster",
                "notification_type": "warning",
            }
        )

        response = await handler.handle_notify(request)

        assert response.status == 200
        body = json.loads(response.body)
        assert body["status"] == "sent"
        assert body["notification_id"] == "test-uuid-123"
        assert body["channel"] == "C9876543210"

    @pytest.mark.asyncio
    async def test_notification_with_all_fields(
        self, handler: NotifyHandler, mock_notification_service: MagicMock
    ) -> None:
        """Test notification with all optional fields."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.remote = "127.0.0.1"
        request.json = AsyncMock(
            return_value={
                "cluster_id": "ocp-prod-01",
                "cluster_name": "Production Cluster",
                "owner_email": "admin@example.com",
                "expiration_date": "2024-03-15T12:00:00Z",
                "notification_type": "warning",
                "message": "Custom message",
            }
        )

        response = await handler.handle_notify(request)

        assert response.status == 200
        mock_notification_service.send_notification.assert_called_once()
        call_kwargs = mock_notification_service.send_notification.call_args.kwargs
        assert call_kwargs["cluster_id"] == "ocp-prod-01"
        assert call_kwargs["custom_message"] == "Custom message"


class TestNotifyFailure:
    """Tests for failed notify requests."""

    @pytest.mark.asyncio
    async def test_slack_error_returns_500(
        self, handler: NotifyHandler, mock_notification_service: MagicMock
    ) -> None:
        """Test that Slack API error returns 500."""
        mock_notification_service.send_notification = AsyncMock(
            return_value=NotificationResult(
                success=False,
                notification_id="test-uuid-123",
                error="Slack API error",
            )
        )

        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.remote = "127.0.0.1"
        request.json = AsyncMock(
            return_value={
                "cluster_id": "ocp-prod-01",
                "cluster_name": "Production Cluster",
                "notification_type": "warning",
            }
        )

        response = await handler.handle_notify(request)

        assert response.status == 500
        body = json.loads(response.body)
        assert body["status"] == "failed"
        assert body["error"] == "Slack API error"
