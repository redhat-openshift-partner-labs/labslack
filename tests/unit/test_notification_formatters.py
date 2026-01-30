"""Unit tests for notification formatters."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from labslack.notifications.formatters import NotificationFormatter


@pytest.fixture
def formatter() -> NotificationFormatter:
    """Create a NotificationFormatter instance."""
    return NotificationFormatter()


class TestWarningFormat:
    """Tests for warning notification formatting."""

    def test_warning_without_expiration_date(self, formatter: NotificationFormatter) -> None:
        """Test warning message without expiration date."""
        message = formatter.format_message(
            cluster_id="ocp-prod-01",
            cluster_name="Production Cluster",
            notification_type="warning",
        )

        assert "ocp-prod-01" in message
        assert "Production Cluster" in message
        assert "48 hours" in message
        assert "Warning" in message

    def test_warning_with_expiration_date(self, formatter: NotificationFormatter) -> None:
        """Test warning message with expiration date."""
        expiration = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

        message = formatter.format_message(
            cluster_id="ocp-prod-01",
            cluster_name="Production Cluster",
            notification_type="warning",
            expiration_date=expiration,
        )

        assert "ocp-prod-01" in message
        assert "Production Cluster" in message
        assert "2024-03-15" in message
        assert "12:00" in message


class TestExpirationFormat:
    """Tests for expiration notification formatting."""

    def test_expiration_message(self, formatter: NotificationFormatter) -> None:
        """Test expiration message format."""
        message = formatter.format_message(
            cluster_id="ocp-test-01",
            cluster_name="Test Cluster",
            notification_type="expiration",
        )

        assert "ocp-test-01" in message
        assert "Test Cluster" in message
        assert "expired" in message.lower() or "Expired" in message


class TestCustomMessage:
    """Tests for custom message formatting."""

    def test_custom_message_used(self, formatter: NotificationFormatter) -> None:
        """Test that custom message is used when provided."""
        custom = "This is a custom alert message"

        message = formatter.format_message(
            cluster_id="ocp-prod-01",
            cluster_name="Production Cluster",
            notification_type="warning",
            custom_message=custom,
        )

        assert custom in message
        assert "ocp-prod-01" in message
        assert "Production Cluster" in message

    def test_custom_message_overrides_default(
        self, formatter: NotificationFormatter
    ) -> None:
        """Test that custom message overrides default formatting."""
        custom = "Custom warning text"

        message = formatter.format_message(
            cluster_id="ocp-prod-01",
            cluster_name="Production Cluster",
            notification_type="warning",
            custom_message=custom,
        )

        assert custom in message
        # Should not contain the standard "48 hours" text
        assert "48 hours" not in message
