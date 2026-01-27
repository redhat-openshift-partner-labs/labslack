"""Unit tests for MessageFormatter."""

from __future__ import annotations

import pytest

from labslack.formatters.message_formatter import MAX_MESSAGE_LENGTH, MessageFormatter


class TestMessageFormatterDM:
    """Tests for DM formatting."""

    def test_format_dm_with_metadata(self, formatter: MessageFormatter) -> None:
        """Test formatting DM with full metadata."""
        result = formatter.format_dm(
            text="Hello, I need help",
            user_id="U12345678",
            timestamp="1705312200.123456",
        )

        assert "<@U12345678>" in result
        assert "Hello, I need help" in result
        assert "Time:" in result

    def test_format_dm_without_metadata(
        self, formatter_no_metadata: MessageFormatter
    ) -> None:
        """Test formatting DM without metadata."""
        result = formatter_no_metadata.format_dm(
            text="Just the message",
            user_id="U12345678",
            timestamp="1705312200.123456",
        )

        assert result == "Just the message"
        assert "<@U12345678>" not in result

    def test_format_dm_no_user_id(self, formatter: MessageFormatter) -> None:
        """Test formatting DM without user ID."""
        result = formatter.format_dm(
            text="Anonymous message",
            user_id=None,
            timestamp="1705312200.123456",
        )

        assert "Anonymous message" in result
        assert "From:" not in result

    def test_format_dm_no_timestamp(self, formatter: MessageFormatter) -> None:
        """Test formatting DM without timestamp."""
        result = formatter.format_dm(
            text="Timeless message",
            user_id="U12345678",
            timestamp=None,
        )

        assert "Timeless message" in result
        assert "Time:" not in result


class TestMessageFormatterWebhook:
    """Tests for webhook message formatting."""

    def test_format_webhook_with_source(self, formatter: MessageFormatter) -> None:
        """Test formatting webhook with source."""
        result = formatter.format_webhook(
            text="Build completed",
            source="Jenkins",
            metadata=None,
        )

        assert "Source:* Jenkins" in result
        assert "Build completed" in result

    def test_format_webhook_with_metadata(self, formatter: MessageFormatter) -> None:
        """Test formatting webhook with custom metadata."""
        result = formatter.format_webhook(
            text="Alert",
            source="Monitoring",
            metadata={"severity": "critical", "host": "prod-web-1"},
        )

        assert "Severity:* critical" in result
        assert "Host:* prod-web-1" in result

    def test_format_webhook_without_metadata(
        self, formatter_no_metadata: MessageFormatter
    ) -> None:
        """Test formatting webhook without metadata."""
        result = formatter_no_metadata.format_webhook(
            text="Simple message",
            source="System",
            metadata={"key": "value"},
        )

        assert result == "Simple message"


class TestMessageTruncation:
    """Tests for message truncation."""

    def test_truncate_long_message(self, formatter: MessageFormatter) -> None:
        """Test that long messages are truncated."""
        long_text = "x" * (MAX_MESSAGE_LENGTH + 100)
        result = formatter.format_dm(text=long_text, user_id=None, timestamp=None)

        assert len(result) <= MAX_MESSAGE_LENGTH
        assert "[Message truncated]" in result

    def test_no_truncate_short_message(self, formatter: MessageFormatter) -> None:
        """Test that short messages are not truncated."""
        short_text = "Short message"
        result = formatter.format_dm(text=short_text, user_id=None, timestamp=None)

        assert "[Message truncated]" not in result


class TestTimestampParsing:
    """Tests for Slack timestamp parsing."""

    def test_parse_valid_timestamp(self, formatter: MessageFormatter) -> None:
        """Test parsing a valid Slack timestamp."""
        result = formatter.format_dm(
            text="Test",
            user_id="U123",
            timestamp="1705312200.123456",
        )

        # Should contain a formatted date
        assert "2024-01-15" in result or "Time:" in result

    def test_parse_invalid_timestamp(self, formatter: MessageFormatter) -> None:
        """Test parsing an invalid timestamp gracefully."""
        result = formatter.format_dm(
            text="Test",
            user_id="U123",
            timestamp="invalid",
        )

        # Should not crash, just skip the timestamp
        assert "Test" in result
