"""Unit tests for MessageRelay service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from slack_sdk.errors import SlackApiError

from labslack.config import Config
from labslack.formatters.message_formatter import MessageFormatter
from labslack.relay.message_relay import MessageRelay


@pytest.fixture
def config() -> Config:
    """Create a test configuration."""
    return Config(
        slack_bot_token="xoxb-test-token",
        slack_signing_secret="test-secret",
        relay_channel_id="C12345678",
        include_metadata=True,
        max_retries=3,
        retry_base_delay=0.1,  # Fast for tests
    )


@pytest.fixture
def mock_client() -> AsyncMock:
    """Create a mock Slack client."""
    client = AsyncMock()
    client.chat_postMessage = AsyncMock(return_value={"ok": True})
    return client


@pytest.fixture
def formatter(config: Config) -> MessageFormatter:
    """Create a message formatter."""
    return MessageFormatter(config)


@pytest.fixture
def relay(config: Config, mock_client: AsyncMock, formatter: MessageFormatter) -> MessageRelay:
    """Create a MessageRelay instance."""
    return MessageRelay(config, mock_client, formatter)


class TestMessageRelaySuccess:
    """Tests for successful message relay."""

    async def test_relay_dm_success(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test successful DM relay."""
        result = await relay.relay_dm(
            text="Hello world",
            user_id="U12345",
            timestamp="1234567890.123456",
        )

        assert result is True
        mock_client.chat_postMessage.assert_called_once()
        call_args = mock_client.chat_postMessage.call_args
        assert call_args.kwargs["channel"] == "C12345678"
        assert "Hello world" in call_args.kwargs["text"]

    async def test_relay_webhook_success(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test successful webhook relay."""
        result = await relay.relay_webhook(
            text="External message",
            source="test-service",
            metadata={"key": "value"},
        )

        assert result is True
        mock_client.chat_postMessage.assert_called_once()


class TestMessageRelayErrorHandling:
    """Tests for Slack API error handling."""

    async def test_channel_not_found_error(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test handling of channel_not_found error (non-retryable)."""
        error_response = {"ok": False, "error": "channel_not_found"}
        mock_client.chat_postMessage.side_effect = SlackApiError(
            message="channel_not_found",
            response=MagicMock(data=error_response, headers={}),
        )

        result = await relay.relay_dm(text="Test", user_id="U12345")

        assert result is False
        # Should not retry for non-retryable errors
        assert mock_client.chat_postMessage.call_count == 1

    async def test_not_in_channel_error(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test handling of not_in_channel error (non-retryable)."""
        error_response = {"ok": False, "error": "not_in_channel"}
        mock_client.chat_postMessage.side_effect = SlackApiError(
            message="not_in_channel",
            response=MagicMock(data=error_response, headers={}),
        )

        result = await relay.relay_dm(text="Test", user_id="U12345")

        assert result is False
        assert mock_client.chat_postMessage.call_count == 1

    async def test_invalid_auth_error(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test handling of invalid_auth error (non-retryable)."""
        error_response = {"ok": False, "error": "invalid_auth"}
        mock_client.chat_postMessage.side_effect = SlackApiError(
            message="invalid_auth",
            response=MagicMock(data=error_response, headers={}),
        )

        result = await relay.relay_dm(text="Test", user_id="U12345")

        assert result is False
        assert mock_client.chat_postMessage.call_count == 1


class TestMessageRelayRetry:
    """Tests for retry logic with exponential backoff."""

    async def test_rate_limited_retries_and_succeeds(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test retry on rate_limited error that eventually succeeds."""
        error_response = {"ok": False, "error": "rate_limited"}
        mock_response = MagicMock(data=error_response)
        mock_response.headers = {"Retry-After": "1"}

        # Fail twice, then succeed
        mock_client.chat_postMessage.side_effect = [
            SlackApiError(message="rate_limited", response=mock_response),
            SlackApiError(message="rate_limited", response=mock_response),
            {"ok": True},
        ]

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await relay.relay_dm(text="Test", user_id="U12345")

        assert result is True
        assert mock_client.chat_postMessage.call_count == 3
        assert mock_sleep.call_count == 2

    async def test_service_unavailable_retries(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test retry on service_unavailable error."""
        error_response = {"ok": False, "error": "service_unavailable"}
        mock_response = MagicMock(data=error_response, headers={})

        # Fail once, then succeed
        mock_client.chat_postMessage.side_effect = [
            SlackApiError(message="service_unavailable", response=mock_response),
            {"ok": True},
        ]

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await relay.relay_dm(text="Test", user_id="U12345")

        assert result is True
        assert mock_client.chat_postMessage.call_count == 2

    async def test_max_retries_exceeded(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test failure after max retries exceeded."""
        error_response = {"ok": False, "error": "rate_limited"}
        mock_response = MagicMock(data=error_response)
        mock_response.headers = {"Retry-After": "1"}

        # Always fail
        mock_client.chat_postMessage.side_effect = SlackApiError(
            message="rate_limited", response=mock_response
        )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await relay.relay_dm(text="Test", user_id="U12345")

        assert result is False
        # Initial attempt + max_retries (3) = 4 total attempts
        assert mock_client.chat_postMessage.call_count == 4

    async def test_exponential_backoff_delays(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test that exponential backoff is applied correctly."""
        error_response = {"ok": False, "error": "request_timeout"}
        mock_response = MagicMock(data=error_response, headers={})

        mock_client.chat_postMessage.side_effect = SlackApiError(
            message="request_timeout", response=mock_response
        )

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await relay.relay_dm(text="Test", user_id="U12345")

        # With retry_base_delay=0.1: delays should be 0.1, 0.2, 0.4
        calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert len(calls) == 3
        assert calls[0] == pytest.approx(0.1, rel=0.1)
        assert calls[1] == pytest.approx(0.2, rel=0.1)
        assert calls[2] == pytest.approx(0.4, rel=0.1)

    async def test_rate_limit_respects_retry_after_header(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test that Retry-After header is respected for rate limiting."""
        error_response = {"ok": False, "error": "rate_limited"}
        mock_response = MagicMock(data=error_response)
        mock_response.headers = {"Retry-After": "5"}

        mock_client.chat_postMessage.side_effect = [
            SlackApiError(message="rate_limited", response=mock_response),
            {"ok": True},
        ]

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await relay.relay_dm(text="Test", user_id="U12345")

        # Should use Retry-After value (5) instead of base delay
        mock_sleep.assert_called_once_with(5)


class TestMessageRelayLogging:
    """Tests for logging behavior."""

    async def test_logs_success(
        self, relay: MessageRelay, mock_client: AsyncMock, caplog
    ) -> None:
        """Test that successful relay is logged."""
        import logging

        with caplog.at_level(logging.INFO):
            await relay.relay_dm(text="Test", user_id="U12345")

        assert any("Relayed DM" in record.message for record in caplog.records)

    async def test_logs_failure(
        self, relay: MessageRelay, mock_client: AsyncMock, caplog
    ) -> None:
        """Test that failed relay is logged."""
        import logging

        error_response = {"ok": False, "error": "channel_not_found"}
        mock_client.chat_postMessage.side_effect = SlackApiError(
            message="channel_not_found",
            response=MagicMock(data=error_response, headers={}),
        )

        with caplog.at_level(logging.ERROR):
            await relay.relay_dm(text="Test", user_id="U12345")

        assert any("Failed to relay" in record.message for record in caplog.records)

    async def test_logs_retry_attempts(
        self, relay: MessageRelay, mock_client: AsyncMock, caplog
    ) -> None:
        """Test that retry attempts are logged."""
        import logging

        error_response = {"ok": False, "error": "rate_limited"}
        mock_response = MagicMock(data=error_response)
        mock_response.headers = {"Retry-After": "1"}

        mock_client.chat_postMessage.side_effect = [
            SlackApiError(message="rate_limited", response=mock_response),
            {"ok": True},
        ]

        with caplog.at_level(logging.WARNING):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await relay.relay_dm(text="Test", user_id="U12345")

        assert any("retry" in record.message.lower() for record in caplog.records)


class TestMessageRelayWebhook:
    """Tests for webhook relay specifics."""

    async def test_relay_webhook_returns_success(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test webhook relay returns True on success."""
        result = await relay.relay_webhook(
            text="Webhook message",
            source="external-service",
        )

        assert result is True

    async def test_relay_webhook_returns_failure(
        self, relay: MessageRelay, mock_client: AsyncMock
    ) -> None:
        """Test webhook relay returns False on failure."""
        error_response = {"ok": False, "error": "channel_not_found"}
        mock_client.chat_postMessage.side_effect = SlackApiError(
            message="channel_not_found",
            response=MagicMock(data=error_response, headers={}),
        )

        result = await relay.relay_webhook(text="Test", source="test")

        assert result is False
