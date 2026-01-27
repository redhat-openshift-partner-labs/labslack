"""Shared pytest fixtures for LabSlack tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from labslack.config import Config
from labslack.formatters.message_formatter import MessageFormatter
from labslack.relay.message_relay import MessageRelay

if TYPE_CHECKING:
    from slack_sdk import WebClient


@pytest.fixture
def config() -> Config:
    """Create a test configuration."""
    return Config(
        slack_bot_token="xoxb-test-token",
        slack_signing_secret="test-signing-secret",
        relay_channel_id="C0123456789",
        include_metadata=True,
        webhook_api_key="test-api-key-123",
        host="localhost",
        port=3000,
        log_level="DEBUG",
    )


@pytest.fixture
def config_no_metadata(config: Config) -> Config:
    """Create a test configuration with metadata disabled."""
    return Config(
        slack_bot_token=config.slack_bot_token,
        slack_signing_secret=config.slack_signing_secret,
        relay_channel_id=config.relay_channel_id,
        include_metadata=False,
        webhook_api_key=config.webhook_api_key,
        host=config.host,
        port=config.port,
        log_level=config.log_level,
    )


@pytest.fixture
def mock_slack_client() -> MagicMock:
    """Create a mock Slack WebClient."""
    client = MagicMock(spec=["chat_postMessage"])
    client.chat_postMessage.return_value = {"ok": True}
    return client


@pytest.fixture
def formatter(config: Config) -> MessageFormatter:
    """Create a MessageFormatter instance."""
    return MessageFormatter(config)


@pytest.fixture
def formatter_no_metadata(config_no_metadata: Config) -> MessageFormatter:
    """Create a MessageFormatter instance with metadata disabled."""
    return MessageFormatter(config_no_metadata)


@pytest.fixture
def relay(
    config: Config,
    mock_slack_client: MagicMock,
    formatter: MessageFormatter,
) -> MessageRelay:
    """Create a MessageRelay instance with mocked client."""
    return MessageRelay(config, mock_slack_client, formatter)
