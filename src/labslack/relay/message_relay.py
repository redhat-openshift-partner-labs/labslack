"""Service for relaying messages to Slack channels."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from slack_sdk.errors import SlackApiError

from labslack.logging import get_logger
from labslack.metrics import get_metrics

if TYPE_CHECKING:
    from slack_sdk.web.async_client import AsyncWebClient

    from labslack.config import Config
    from labslack.formatters.message_formatter import MessageFormatter

# Errors that should trigger a retry
RETRYABLE_ERRORS = frozenset({
    "rate_limited",
    "service_unavailable",
    "request_timeout",
    "internal_error",
})

# Errors that should not be retried
NON_RETRYABLE_ERRORS = frozenset({
    "channel_not_found",
    "not_in_channel",
    "invalid_auth",
    "token_revoked",
    "account_inactive",
    "missing_scope",
})


class MessageRelay:
    """Relays formatted messages to the configured Slack channel."""

    def __init__(
        self,
        config: Config,
        client: AsyncWebClient,
        formatter: MessageFormatter,
    ) -> None:
        self.config = config
        self.client = client
        self.formatter = formatter
        self.logger = get_logger("message_relay")
        self.metrics = get_metrics()
        self._relay_counter = self.metrics.counter(
            "messages_relayed_total", "Total messages relayed"
        )
        self._retry_counter = self.metrics.counter(
            "relay_retries_total", "Total relay retry attempts"
        )
        self._error_counter = self.metrics.counter(
            "relay_errors_total", "Total relay errors"
        )

    async def relay_dm(
        self,
        text: str,
        user_id: str | None = None,
        timestamp: str | None = None,
    ) -> bool:
        """Relay a direct message to the configured channel.

        Args:
            text: The message text.
            user_id: The Slack user ID who sent the message.
            timestamp: The message timestamp.

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        self.logger.debug(
            "Relaying DM",
            extra={"user_id": user_id, "source": "dm"},
        )
        formatted = self.formatter.format_dm(
            text=text,
            user_id=user_id,
            timestamp=timestamp,
        )
        success = await self._send_message_with_retry(formatted, source="dm")

        if success:
            self._relay_counter.labels(source="dm", status="success").inc()
            self.logger.info(
                "Relayed DM successfully",
                extra={"user_id": user_id, "source": "dm"},
            )
        else:
            self._relay_counter.labels(source="dm", status="failed").inc()
            self.logger.error(
                "Failed to relay DM",
                extra={"user_id": user_id, "source": "dm"},
            )

        return success

    async def relay_webhook(
        self,
        text: str,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Relay a webhook message to the configured channel.

        Args:
            text: The message text.
            source: The source identifier for the webhook.
            metadata: Optional metadata to include.

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        self.logger.debug(
            "Relaying webhook",
            extra={"webhook_source": source, "source": "webhook"},
        )
        formatted = self.formatter.format_webhook(
            text=text,
            source=source,
            metadata=metadata,
        )
        success = await self._send_message_with_retry(formatted, source="webhook")

        if success:
            self._relay_counter.labels(source="webhook", status="success").inc()
            self.logger.info(
                "Relayed webhook successfully",
                extra={"webhook_source": source, "source": "webhook"},
            )
        else:
            self._relay_counter.labels(source="webhook", status="failed").inc()
            self.logger.error(
                "Failed to relay webhook",
                extra={"webhook_source": source, "source": "webhook"},
            )

        return success

    def _is_retryable_error(self, error_code: str) -> bool:
        """Check if an error code should trigger a retry.

        Args:
            error_code: The Slack API error code.

        Returns:
            True if the error is retryable, False otherwise.
        """
        return error_code in RETRYABLE_ERRORS

    def _get_retry_delay(self, attempt: int, error: SlackApiError) -> float:
        """Calculate the delay before the next retry attempt.

        For rate_limited errors, respects the Retry-After header.
        Otherwise, uses exponential backoff.

        Args:
            attempt: The current attempt number (0-indexed).
            error: The Slack API error.

        Returns:
            The delay in seconds before the next retry.
        """
        error_code = error.response.data.get("error", "")

        if error_code == "rate_limited":
            # Respect Retry-After header for rate limiting
            retry_after = error.response.headers.get("Retry-After")
            if retry_after:
                return float(int(retry_after))

        # Exponential backoff: base_delay * 2^attempt
        return float(self.config.retry_base_delay * (2 ** attempt))

    async def _send_message_with_retry(self, text: str, source: str = "unknown") -> bool:
        """Send a message to the relay channel with retry logic.

        Implements exponential backoff for retryable errors.

        Args:
            text: The formatted message text.
            source: The source type for metrics labeling.

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        if not self.config.relay_channel_id:
            self.logger.error(
                "Cannot send message: relay_channel_id not configured",
                extra={"source": source},
            )
            self._error_counter.labels(source=source, error="no_channel").inc()
            return False

        for attempt in range(self.config.max_retries + 1):
            try:
                await self.client.chat_postMessage(
                    channel=self.config.relay_channel_id,
                    text=text,
                )
                return True

            except SlackApiError as e:
                error_code = e.response.data.get("error", "unknown")

                if not self._is_retryable_error(error_code):
                    self.logger.error(
                        "Slack API error (non-retryable)",
                        extra={
                            "error_code": error_code,
                            "source": source,
                            "retryable": False,
                        },
                    )
                    self._error_counter.labels(source=source, error=error_code).inc()
                    return False

                if attempt < self.config.max_retries:
                    delay = self._get_retry_delay(attempt, e)
                    self._retry_counter.labels(source=source, error=error_code).inc()
                    self.logger.warning(
                        "Slack API error, retrying",
                        extra={
                            "error_code": error_code,
                            "attempt": attempt + 1,
                            "max_retries": self.config.max_retries,
                            "delay_seconds": delay,
                            "source": source,
                        },
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        "Slack API error after max retries",
                        extra={
                            "error_code": error_code,
                            "max_retries": self.config.max_retries,
                            "source": source,
                        },
                    )
                    self._error_counter.labels(source=source, error=error_code).inc()

        return False
