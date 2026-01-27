"""Unit tests for WebhookHandler."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from labslack.config import Config
from labslack.handlers.webhook_handler import WebhookHandler

if TYPE_CHECKING:
    from labslack.relay.message_relay import MessageRelay


@pytest.fixture
def mock_relay() -> MagicMock:
    """Create a mock MessageRelay."""
    relay = MagicMock()
    relay.relay_webhook = AsyncMock()
    return relay


@pytest.fixture
def webhook_handler(config: Config, mock_relay: MagicMock) -> WebhookHandler:
    """Create a WebhookHandler instance."""
    return WebhookHandler(config, mock_relay)


class TestWebhookAuthentication:
    """Tests for webhook authentication."""

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_401(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test that missing API key returns 401."""
        request = MagicMock()
        request.headers = {}
        request.json = AsyncMock(return_value={"message": "test"})

        response = await webhook_handler.handle_webhook(request)

        assert response.status == 401
        body = json.loads(response.body)
        assert body["error"] == "Unauthorized"

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_401(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test that invalid API key returns 401."""
        request = MagicMock()
        request.headers = {"X-API-Key": "wrong-key"}
        request.json = AsyncMock(return_value={"message": "test"})

        response = await webhook_handler.handle_webhook(request)

        assert response.status == 401

    @pytest.mark.asyncio
    async def test_valid_api_key_succeeds(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test that valid API key allows request."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.json = AsyncMock(return_value={"message": "test"})

        response = await webhook_handler.handle_webhook(request)

        assert response.status == 200


class TestWebhookValidation:
    """Tests for webhook payload validation."""

    @pytest.mark.asyncio
    async def test_missing_message_returns_400(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test that missing message field returns 400."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.json = AsyncMock(return_value={"source": "test"})

        response = await webhook_handler.handle_webhook(request)

        assert response.status == 400
        body = json.loads(response.body)
        assert "message" in body["error"].lower()

    @pytest.mark.asyncio
    async def test_empty_message_returns_400(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test that empty message returns 400."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.json = AsyncMock(return_value={"message": "  "})

        response = await webhook_handler.handle_webhook(request)

        assert response.status == 400
        body = json.loads(response.body)
        assert "empty" in body["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_json_returns_400(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test that invalid JSON returns 400."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.json = AsyncMock(side_effect=json.JSONDecodeError("", "", 0))

        response = await webhook_handler.handle_webhook(request)

        assert response.status == 400
        body = json.loads(response.body)
        assert "json" in body["error"].lower()


class TestWebhookRelay:
    """Tests for webhook message relay."""

    @pytest.mark.asyncio
    async def test_valid_message_is_relayed(
        self, webhook_handler: WebhookHandler, mock_relay: MagicMock
    ) -> None:
        """Test that valid message is relayed."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.json = AsyncMock(
            return_value={"message": "Deploy completed", "source": "CI/CD"}
        )

        await webhook_handler.handle_webhook(request)

        mock_relay.relay_webhook.assert_called_once_with(
            text="Deploy completed",
            source="CI/CD",
            metadata={},
        )

    @pytest.mark.asyncio
    async def test_metadata_is_passed(
        self, webhook_handler: WebhookHandler, mock_relay: MagicMock
    ) -> None:
        """Test that additional metadata is passed to relay."""
        request = MagicMock()
        request.headers = {"X-API-Key": "test-api-key-123"}
        request.json = AsyncMock(
            return_value={
                "message": "Alert",
                "source": "Monitor",
                "severity": "high",
                "host": "prod-1",
            }
        )

        await webhook_handler.handle_webhook(request)

        mock_relay.relay_webhook.assert_called_once()
        call_kwargs = mock_relay.relay_webhook.call_args.kwargs
        assert call_kwargs["metadata"] == {"severity": "high", "host": "prod-1"}


class TestHealthCheck:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(
        self, webhook_handler: WebhookHandler
    ) -> None:
        """Test that health check returns 200."""
        request = MagicMock()

        response = await webhook_handler.health_check(request)

        assert response.status == 200
        body = json.loads(response.body)
        assert body["status"] == "healthy"
