"""BDD test fixtures and step definitions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_bdd import given, parsers, then, when

from labslack.config import Config
from labslack.formatters.message_formatter import MessageFormatter
from labslack.handlers.webhook_handler import WebhookHandler
from labslack.relay.message_relay import MessageRelay


# Shared BDD fixtures
@pytest.fixture
def bdd_config() -> Config:
    """BDD test configuration."""
    return Config(
        slack_bot_token="xoxb-test-token",
        slack_signing_secret="test-signing-secret",
        relay_channel_id="C0123456789",
        include_metadata=True,
        webhook_api_key="test-api-key-123",
    )


@pytest.fixture
def bdd_mock_client() -> MagicMock:
    """BDD mock Slack client."""
    client = MagicMock()
    client.chat_postMessage.return_value = {"ok": True}
    return client


@pytest.fixture
def bdd_formatter(bdd_config: Config) -> MessageFormatter:
    """BDD MessageFormatter."""
    return MessageFormatter(bdd_config)


@pytest.fixture
def bdd_relay(
    bdd_config: Config, bdd_mock_client: MagicMock, bdd_formatter: MessageFormatter
) -> MessageRelay:
    """BDD MessageRelay."""
    return MessageRelay(bdd_config, bdd_mock_client, bdd_formatter)


@pytest.fixture
def bdd_webhook_handler(bdd_config: Config, bdd_relay: MessageRelay) -> WebhookHandler:
    """BDD WebhookHandler."""
    return WebhookHandler(bdd_config, bdd_relay)


# Shared context for BDD scenarios
@pytest.fixture
def bdd_context() -> dict:
    """Shared context dict for passing data between BDD steps."""
    return {}
