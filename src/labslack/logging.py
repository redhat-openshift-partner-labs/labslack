"""Structured logging module for LabSlack.

Provides JSON-formatted logging with contextual fields for observability.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    # Fields from LogRecord to exclude from extras
    RESERVED_ATTRS = frozenset([
        "args", "asctime", "created", "exc_info", "exc_text", "filename",
        "funcName", "levelname", "levelno", "lineno", "module", "msecs",
        "message", "msg", "name", "pathname", "process", "processName",
        "relativeCreated", "stack_info", "taskName", "thread", "threadName",
    ])

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.

        Args:
            record: The log record to format.

        Returns:
            JSON string representation of the log record.
        """
        # Build base log entry
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=UTC
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add stack info if present
        if record.stack_info:
            log_entry["stack_info"] = record.stack_info

        # Add extra fields (user-provided context)
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_ATTRS and not key.startswith("_"):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


def configure_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> None:
    """Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: If True, use JSON formatting. Otherwise, use text format.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Get the root labslack logger
    logger = logging.getLogger("labslack")
    logger.setLevel(log_level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Set formatter
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the labslack namespace.

    Args:
        name: The module name for the logger.

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(f"labslack.{name}")
