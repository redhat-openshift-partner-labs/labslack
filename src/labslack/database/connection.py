"""Async SQLite database connection management."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import aiosqlite

from labslack.database.models import NotificationHistory

if TYPE_CHECKING:
    from labslack.config import Config


# Module-level connection pool (single connection for SQLite)
_db_connection: aiosqlite.Connection | None = None

# SQL schema for notification history
_SCHEMA = """
CREATE TABLE IF NOT EXISTS notification_history (
    id TEXT PRIMARY KEY,
    cluster_id TEXT NOT NULL,
    cluster_name TEXT NOT NULL,
    notification_type TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    slack_channel TEXT,
    slack_ts TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_cluster
    ON notification_history(cluster_id);

CREATE INDEX IF NOT EXISTS idx_notification_created
    ON notification_history(created_at);
"""


async def init_database(config: Config) -> None:
    """Initialize the database connection and create schema.

    Args:
        config: Application configuration containing database_path.
    """
    global _db_connection

    if _db_connection is not None:
        return

    # Ensure the directory exists
    db_path = Path(config.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    _db_connection = await aiosqlite.connect(str(db_path))
    _db_connection.row_factory = aiosqlite.Row

    # Create schema
    await _db_connection.executescript(_SCHEMA)
    await _db_connection.commit()


async def get_database() -> aiosqlite.Connection:
    """Get the database connection.

    Returns:
        The active database connection.

    Raises:
        RuntimeError: If database has not been initialized.
    """
    if _db_connection is None:
        raise RuntimeError("Database not initialized. Call init_database first.")
    return _db_connection


async def close_database() -> None:
    """Close the database connection."""
    global _db_connection

    if _db_connection is not None:
        await _db_connection.close()
        _db_connection = None


async def save_notification(notification: NotificationHistory) -> None:
    """Save a notification record to the database.

    Args:
        notification: The notification to save.
    """
    db = await get_database()
    await db.execute(
        """
        INSERT INTO notification_history
        (id, cluster_id, cluster_name, notification_type, message, status,
         error_message, slack_channel, slack_ts, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            notification.id,
            notification.cluster_id,
            notification.cluster_name,
            notification.notification_type,
            notification.message,
            notification.status.value,
            notification.error_message,
            notification.slack_channel,
            notification.slack_ts,
            notification.created_at.isoformat(),
        ),
    )
    await db.commit()


async def get_notification_by_id(notification_id: str) -> NotificationHistory | None:
    """Retrieve a notification by ID.

    Args:
        notification_id: The notification ID to look up.

    Returns:
        The notification record or None if not found.
    """
    db = await get_database()
    cursor = await db.execute(
        """
        SELECT id, cluster_id, cluster_name, notification_type, message,
               status, error_message, slack_channel, slack_ts, created_at
        FROM notification_history
        WHERE id = ?
        """,
        (notification_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return NotificationHistory.from_row(tuple(row))


async def get_notifications_by_cluster(
    cluster_id: str, limit: int = 100
) -> list[NotificationHistory]:
    """Retrieve notifications for a specific cluster.

    Args:
        cluster_id: The cluster ID to filter by.
        limit: Maximum number of records to return.

    Returns:
        List of notification records.
    """
    db = await get_database()
    cursor = await db.execute(
        """
        SELECT id, cluster_id, cluster_name, notification_type, message,
               status, error_message, slack_channel, slack_ts, created_at
        FROM notification_history
        WHERE cluster_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (cluster_id, limit),
    )
    rows = await cursor.fetchall()
    return [NotificationHistory.from_row(tuple(row)) for row in rows]
