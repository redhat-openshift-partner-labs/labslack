"""Unit tests for database module."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from labslack.config import Config
from labslack.database.connection import (
    close_database,
    get_database,
    get_notification_by_id,
    get_notifications_by_cluster,
    init_database,
    save_notification,
)
from labslack.database.models import NotificationHistory, NotificationStatus


@pytest.fixture
def config_with_memory_db() -> Config:
    """Create a test config with in-memory database."""
    return Config(
        slack_bot_token="xoxb-test-token",
        slack_signing_secret="test-signing-secret",
        database_path=":memory:",
    )


@pytest.fixture
async def initialized_db(config_with_memory_db: Config):
    """Initialize in-memory database for testing."""
    # Close any existing connection
    await close_database()
    await init_database(config_with_memory_db)
    yield
    await close_database()


class TestNotificationHistoryModel:
    """Tests for NotificationHistory model."""

    def test_create_notification(self) -> None:
        """Test creating a notification with generated ID and timestamp."""
        notification = NotificationHistory.create(
            cluster_id="ocp-prod-01",
            cluster_name="Production Cluster",
            notification_type="warning",
            message="Test message",
            status=NotificationStatus.SENT,
            slack_channel="C123456789",
            slack_ts="1234567890.123456",
        )

        assert notification.id is not None
        assert len(notification.id) == 36  # UUID format
        assert notification.cluster_id == "ocp-prod-01"
        assert notification.status == NotificationStatus.SENT
        assert notification.created_at is not None

    def test_to_dict(self) -> None:
        """Test converting notification to dictionary."""
        notification = NotificationHistory.create(
            cluster_id="ocp-prod-01",
            cluster_name="Production Cluster",
            notification_type="warning",
            message="Test message",
            status=NotificationStatus.SENT,
        )

        data = notification.to_dict()

        assert data["cluster_id"] == "ocp-prod-01"
        assert data["status"] == "sent"
        assert isinstance(data["created_at"], str)

    def test_from_row(self) -> None:
        """Test creating notification from database row."""
        row = (
            "test-uuid",
            "ocp-prod-01",
            "Production Cluster",
            "warning",
            "Test message",
            "sent",
            None,  # error_message
            "C123456789",  # slack_channel
            "1234567890.123456",  # slack_ts
            "2024-03-13T12:00:00",  # created_at
        )

        notification = NotificationHistory.from_row(row)

        assert notification.id == "test-uuid"
        assert notification.cluster_id == "ocp-prod-01"
        assert notification.status == NotificationStatus.SENT
        assert notification.created_at == datetime(2024, 3, 13, 12, 0, 0)


class TestDatabaseOperations:
    """Tests for database operations."""

    @pytest.mark.asyncio
    async def test_init_database(self, initialized_db) -> None:
        """Test database initialization."""
        db = await get_database()
        assert db is not None

    @pytest.mark.asyncio
    async def test_get_database_without_init_raises(self) -> None:
        """Test that get_database raises if not initialized."""
        await close_database()
        with pytest.raises(RuntimeError, match="not initialized"):
            await get_database()

    @pytest.mark.asyncio
    async def test_save_and_retrieve_notification(self, initialized_db) -> None:
        """Test saving and retrieving a notification."""
        notification = NotificationHistory.create(
            cluster_id="ocp-test-01",
            cluster_name="Test Cluster",
            notification_type="warning",
            message="Test message",
            status=NotificationStatus.SENT,
            slack_channel="C123456789",
            slack_ts="1234567890.123456",
        )

        await save_notification(notification)

        retrieved = await get_notification_by_id(notification.id)

        assert retrieved is not None
        assert retrieved.id == notification.id
        assert retrieved.cluster_id == "ocp-test-01"
        assert retrieved.status == NotificationStatus.SENT

    @pytest.mark.asyncio
    async def test_get_notification_not_found(self, initialized_db) -> None:
        """Test retrieving non-existent notification."""
        result = await get_notification_by_id("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_notifications_by_cluster(self, initialized_db) -> None:
        """Test retrieving notifications by cluster ID."""
        # Create multiple notifications for the same cluster
        for i in range(3):
            notification = NotificationHistory.create(
                cluster_id="ocp-prod-01",
                cluster_name="Production Cluster",
                notification_type="warning",
                message=f"Message {i}",
                status=NotificationStatus.SENT,
            )
            await save_notification(notification)

        # Create one for a different cluster
        other = NotificationHistory.create(
            cluster_id="ocp-test-01",
            cluster_name="Test Cluster",
            notification_type="warning",
            message="Other",
            status=NotificationStatus.SENT,
        )
        await save_notification(other)

        results = await get_notifications_by_cluster("ocp-prod-01")

        assert len(results) == 3
        assert all(n.cluster_id == "ocp-prod-01" for n in results)

    @pytest.mark.asyncio
    async def test_get_notifications_by_cluster_with_limit(
        self, initialized_db
    ) -> None:
        """Test retrieving notifications with limit."""
        for i in range(5):
            notification = NotificationHistory.create(
                cluster_id="ocp-prod-01",
                cluster_name="Production Cluster",
                notification_type="warning",
                message=f"Message {i}",
                status=NotificationStatus.SENT,
            )
            await save_notification(notification)

        results = await get_notifications_by_cluster("ocp-prod-01", limit=2)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_save_failed_notification(self, initialized_db) -> None:
        """Test saving a failed notification with error message."""
        notification = NotificationHistory.create(
            cluster_id="ocp-prod-01",
            cluster_name="Production Cluster",
            notification_type="warning",
            message="Test message",
            status=NotificationStatus.FAILED,
            error_message="Slack API error",
        )

        await save_notification(notification)

        retrieved = await get_notification_by_id(notification.id)

        assert retrieved is not None
        assert retrieved.status == NotificationStatus.FAILED
        assert retrieved.error_message == "Slack API error"
