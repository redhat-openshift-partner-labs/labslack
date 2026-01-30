"""Database models for notification history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Self
from uuid import uuid4


class NotificationStatus(str, Enum):
    """Status of a notification."""

    SENT = "sent"
    FAILED = "failed"


@dataclass
class NotificationHistory:
    """Record of a cluster notification."""

    id: str
    cluster_id: str
    cluster_name: str
    notification_type: str
    message: str
    status: NotificationStatus
    created_at: datetime
    error_message: str | None = None
    slack_channel: str | None = None
    slack_ts: str | None = None

    @classmethod
    def create(
        cls,
        cluster_id: str,
        cluster_name: str,
        notification_type: str,
        message: str,
        status: NotificationStatus,
        error_message: str | None = None,
        slack_channel: str | None = None,
        slack_ts: str | None = None,
    ) -> Self:
        """Create a new NotificationHistory record with generated ID and timestamp."""
        return cls(
            id=str(uuid4()),
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            notification_type=notification_type,
            message=message,
            status=status,
            created_at=datetime.now(timezone.utc),
            error_message=error_message,
            slack_channel=slack_channel,
            slack_ts=slack_ts,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster_name,
            "notification_type": self.notification_type,
            "message": self.message,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "error_message": self.error_message,
            "slack_channel": self.slack_channel,
            "slack_ts": self.slack_ts,
        }

    @classmethod
    def from_row(cls, row: tuple) -> Self:
        """Create NotificationHistory from a database row."""
        return cls(
            id=row[0],
            cluster_id=row[1],
            cluster_name=row[2],
            notification_type=row[3],
            message=row[4],
            status=NotificationStatus(row[5]),
            error_message=row[6],
            slack_channel=row[7],
            slack_ts=row[8],
            created_at=datetime.fromisoformat(row[9]),
        )
