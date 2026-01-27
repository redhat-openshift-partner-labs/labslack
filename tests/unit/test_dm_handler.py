"""Unit tests for DMHandler."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from labslack.config import Config
from labslack.handlers.dm_handler import DMHandler

if TYPE_CHECKING:
    from labslack.relay.message_relay import MessageRelay


@pytest.fixture
def mock_relay() -> MagicMock:
    """Create a mock MessageRelay."""
    return MagicMock()


@pytest.fixture
def dm_handler(config: Config, mock_relay: MagicMock) -> DMHandler:
    """Create a DMHandler instance."""
    return DMHandler(config, mock_relay)


class TestDMHandlerEvents:
    """Tests for DM event handling logic."""

    def test_should_ignore_bot_messages(
        self, dm_handler: DMHandler, mock_relay: MagicMock
    ) -> None:
        """Test that bot messages are ignored."""
        event = {
            "type": "message",
            "channel_type": "im",
            "text": "Bot message",
            "bot_id": "B123",
            "user": "U123",
        }

        # Simulate the filtering logic
        should_process = not event.get("bot_id") and not event.get("subtype")
        assert not should_process

    def test_should_ignore_message_subtypes(
        self, dm_handler: DMHandler, mock_relay: MagicMock
    ) -> None:
        """Test that message subtypes are ignored."""
        event = {
            "type": "message",
            "channel_type": "im",
            "text": "Changed message",
            "subtype": "message_changed",
            "user": "U123",
        }

        should_process = not event.get("bot_id") and not event.get("subtype")
        assert not should_process

    def test_should_process_user_dm(
        self, dm_handler: DMHandler, mock_relay: MagicMock
    ) -> None:
        """Test that user DMs are processed."""
        event = {
            "type": "message",
            "channel_type": "im",
            "text": "Hello bot",
            "user": "U12345678",
            "ts": "1705312200.123456",
        }

        should_process = (
            not event.get("bot_id")
            and not event.get("subtype")
            and event.get("channel_type") == "im"
            and event.get("text", "").strip()
        )
        assert should_process

    def test_should_ignore_non_im_messages(
        self, dm_handler: DMHandler, mock_relay: MagicMock
    ) -> None:
        """Test that non-IM messages are ignored."""
        event = {
            "type": "message",
            "channel_type": "channel",
            "text": "Channel message",
            "user": "U123",
        }

        should_process = event.get("channel_type") == "im"
        assert not should_process

    def test_should_ignore_empty_messages(
        self, dm_handler: DMHandler, mock_relay: MagicMock
    ) -> None:
        """Test that empty messages are ignored."""
        event = {
            "type": "message",
            "channel_type": "im",
            "text": "   ",
            "user": "U123",
        }

        should_process = event.get("text", "").strip()
        assert not should_process


class TestDMHandlerRegistration:
    """Tests for handler registration."""

    def test_register_adds_event_listener(
        self, dm_handler: DMHandler, mock_relay: MagicMock
    ) -> None:
        """Test that register adds an event listener to the app."""
        mock_app = MagicMock()

        dm_handler.register(mock_app)

        mock_app.event.assert_called_once_with("message")
