"""Tests for structured logging module."""

import json
import logging

from labslack.logging import (
    JsonFormatter,
    configure_logging,
    get_logger,
)


class TestJsonFormatter:
    """Tests for JSON log formatter."""

    def test_formats_message_as_json(self) -> None:
        """Test that log messages are formatted as valid JSON."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"

    def test_includes_timestamp(self) -> None:
        """Test that timestamp is included in output."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "timestamp" in parsed
        assert isinstance(parsed["timestamp"], str)

    def test_includes_extra_fields(self) -> None:
        """Test that extra context fields are included."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.user_id = "U12345"
        record.source = "webhook"

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["user_id"] == "U12345"
        assert parsed["source"] == "webhook"

    def test_includes_exception_info(self) -> None:
        """Test that exception info is included when present."""
        formatter = JsonFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
        assert "Test error" in parsed["exception"]


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_configure_json_format(self) -> None:
        """Test that JSON format can be configured."""
        configure_logging(level="INFO", json_format=True)

        # Just verify no exception is raised
        assert True

    def test_configure_log_level(self) -> None:
        """Test that log level is properly set."""
        configure_logging(level="DEBUG", json_format=False)

        logger = logging.getLogger("labslack")
        assert logger.level == logging.DEBUG

    def test_configure_text_format(self) -> None:
        """Test that text format can be configured."""
        configure_logging(level="INFO", json_format=False)
        # Just verify no exception is raised
        assert True


class TestGetLogger:
    """Tests for logger retrieval with context."""

    def test_get_logger_returns_logger(self) -> None:
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert "test_module" in logger.name

    def test_get_logger_with_context(self) -> None:
        """Test that context can be bound to logger."""
        logger = get_logger("test_module")

        # Should be able to log with extra context
        logger.info("Test message", extra={"request_id": "abc123"})
        # No exception means success
        assert True
