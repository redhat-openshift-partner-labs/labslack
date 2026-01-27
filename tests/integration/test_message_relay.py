"""Integration tests for message relay flow."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from labslack.app import create_app
from labslack.config import Config


@pytest.fixture
def test_config() -> Config:
    """Test configuration."""
    return Config(
        slack_bot_token="xoxb-test-token",
        slack_signing_secret="test-signing-secret",
        relay_channel_id="C0123456789",
        include_metadata=True,
        webhook_api_key="test-api-key",
    )


class TestDMRelayIntegration:
    """Integration tests for DM to channel relay."""

    @pytest.mark.asyncio
    async def test_dm_event_triggers_relay(self, test_config: Config) -> None:
        """Test that receiving a DM event triggers a message relay."""
        with patch("labslack.app.MessageRelay") as MockRelay:
            mock_relay_instance = MagicMock()
            MockRelay.return_value = mock_relay_instance

            bolt_app, aiohttp_app = create_app(test_config)

            # Simulate a DM event
            event = {
                "type": "message",
                "channel_type": "im",
                "text": "Hello, I need help!",
                "user": "U12345678",
                "ts": "1705312200.123456",
                "channel": "D87654321",
            }

            # Find and call the message handler directly
            # The handler is registered on the bolt_app
            handlers = bolt_app._listeners.get("message", [])
            assert len(handlers) > 0, "No message handlers registered"

            # Create mock context
            say = AsyncMock()
            client = AsyncMock()

            # Call the handler
            for handler in handlers:
                await handler.run_ack_function(event=event, say=say, client=client)

            # Verify relay was called
            mock_relay_instance.relay_dm.assert_called_once_with(
                text="Hello, I need help!",
                user_id="U12345678",
                timestamp="1705312200.123456",
            )

    @pytest.mark.asyncio
    async def test_bot_message_ignored(self, test_config: Config) -> None:
        """Test that bot messages are not relayed."""
        with patch("labslack.app.MessageRelay") as MockRelay:
            mock_relay_instance = MagicMock()
            MockRelay.return_value = mock_relay_instance

            bolt_app, aiohttp_app = create_app(test_config)

            # Simulate a bot message event
            event = {
                "type": "message",
                "channel_type": "im",
                "text": "I am a bot",
                "bot_id": "B12345678",
                "ts": "1705312200.123456",
            }

            handlers = bolt_app._listeners.get("message", [])
            say = AsyncMock()
            client = AsyncMock()

            for handler in handlers:
                await handler.run_ack_function(event=event, say=say, client=client)

            # Verify relay was NOT called
            mock_relay_instance.relay_dm.assert_not_called()

    @pytest.mark.asyncio
    async def test_channel_message_ignored(self, test_config: Config) -> None:
        """Test that channel messages (not DMs) are not relayed."""
        with patch("labslack.app.MessageRelay") as MockRelay:
            mock_relay_instance = MagicMock()
            MockRelay.return_value = mock_relay_instance

            bolt_app, aiohttp_app = create_app(test_config)

            # Simulate a channel message (not DM)
            event = {
                "type": "message",
                "channel_type": "channel",
                "text": "This is in a channel",
                "user": "U12345678",
                "ts": "1705312200.123456",
            }

            handlers = bolt_app._listeners.get("message", [])
            say = AsyncMock()
            client = AsyncMock()

            for handler in handlers:
                await handler.run_ack_function(event=event, say=say, client=client)

            # Verify relay was NOT called
            mock_relay_instance.relay_dm.assert_not_called()


class TestWebhookRelayIntegration:
    """Integration tests for webhook to channel relay."""

    @pytest.mark.asyncio
    async def test_webhook_triggers_relay(self, test_config: Config) -> None:
        """Test that a valid webhook triggers message relay."""
        with patch("labslack.app.MessageRelay") as MockRelay:
            mock_relay_instance = MagicMock()
            mock_relay_instance.relay_webhook = AsyncMock()
            MockRelay.return_value = mock_relay_instance

            bolt_app, aiohttp_app = create_app(test_config)

            # Create test client
            from aiohttp.test_utils import TestClient, TestServer

            async with TestClient(TestServer(aiohttp_app)) as client:
                response = await client.post(
                    "/webhook",
                    json={"message": "Deploy complete", "source": "CI/CD"},
                    headers={"X-API-Key": "test-api-key"},
                )

                assert response.status == 200
                data = await response.json()
                assert data["status"] == "ok"

                mock_relay_instance.relay_webhook.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_without_auth_rejected(self, test_config: Config) -> None:
        """Test that webhooks without auth are rejected."""
        bolt_app, aiohttp_app = create_app(test_config)

        from aiohttp.test_utils import TestClient, TestServer

        async with TestClient(TestServer(aiohttp_app)) as client:
            response = await client.post(
                "/webhook",
                json={"message": "Deploy complete"},
            )

            assert response.status == 401


class TestHealthCheck:
    """Integration tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, test_config: Config) -> None:
        """Test health check endpoint."""
        bolt_app, aiohttp_app = create_app(test_config)

        from aiohttp.test_utils import TestClient, TestServer

        async with TestClient(TestServer(aiohttp_app)) as client:
            response = await client.get("/health")

            assert response.status == 200
            data = await response.json()
            assert data["status"] == "healthy"
