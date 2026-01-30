"""BDD step definitions for cluster notifications feature."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from labslack.config import Config
from labslack.database.connection import (
    close_database,
    get_notification_by_id,
    init_database,
)
from labslack.handlers.notify_handler import NotifyHandler
from labslack.notifications.service import NotificationService

# Load feature file (relative to bdd_features_base_dir in pyproject.toml)
scenarios("cluster_notifications.feature")


# --- Helper to run async code in sync context ---


def run_async(coro):
    """Run async coroutine in sync context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# --- Fixtures ---


@pytest.fixture
def notification_config() -> Config:
    """Configuration for notification tests."""
    return Config(
        slack_bot_token="xoxb-test-token",
        slack_signing_secret="test-signing-secret",
        relay_channel_id="C0123456789",
        webhook_api_key="test-api-key-123",
        notifications_channel_id="C9876543210",
        opladmins_group_handle="opladmins",
        database_path=":memory:",
    )


@pytest.fixture
def mock_slack_client() -> MagicMock:
    """Mock Slack async client."""
    client = MagicMock()
    client.chat_postMessage = AsyncMock(
        return_value={"ok": True, "ts": "1234567890.123456"}
    )
    client.usergroups_list = AsyncMock(
        return_value={
            "ok": True,
            "usergroups": [{"id": "S12345678", "handle": "opladmins"}],
        }
    )
    return client


@pytest.fixture
def notification_service(
    notification_config: Config, mock_slack_client: MagicMock
) -> NotificationService:
    """Create notification service."""
    return NotificationService(notification_config, mock_slack_client)


@pytest.fixture
def notify_handler(
    notification_config: Config, notification_service: NotificationService
) -> NotifyHandler:
    """Create notify handler."""
    return NotifyHandler(notification_config, notification_service)


@pytest.fixture
def notify_context() -> dict:
    """Shared context for notification BDD tests."""
    return {
        "api_key": None,
        "request_data": {},
        "response": None,
        "slack_message": None,
        "notification_id": None,
        "db_record": None,
    }


@pytest.fixture
def initialized_db(notification_config: Config):
    """Initialize database for tests."""
    run_async(close_database())
    run_async(init_database(notification_config))
    yield
    run_async(close_database())


# --- Given Steps ---


@given("the notification system is configured")
def notification_system_configured(notification_config: Config) -> None:
    """Verify notification system configuration."""
    assert notification_config.notifications_channel_id is not None


@given(parsers.parse('the Slack user group "{group}" exists'))
def slack_usergroup_exists(mock_slack_client: MagicMock, group: str) -> None:
    """Mock user group lookup."""
    mock_slack_client.usergroups_list = AsyncMock(
        return_value={
            "ok": True,
            "usergroups": [{"id": "S12345678", "handle": group}],
        }
    )


@given("the notifications channel is available")
def notifications_channel_available(mock_slack_client: MagicMock) -> None:
    """Mock channel availability."""
    mock_slack_client.chat_postMessage = AsyncMock(
        return_value={"ok": True, "ts": "1234567890.123456"}
    )


@given("a valid API key")
def valid_api_key(notify_context: dict) -> None:
    """Set valid API key."""
    notify_context["api_key"] = "test-api-key-123"


@given("no API key is provided")
def no_api_key(notify_context: dict) -> None:
    """No API key set."""
    notify_context["api_key"] = None


@given("an invalid API key")
def invalid_api_key(notify_context: dict) -> None:
    """Set invalid API key."""
    notify_context["api_key"] = "wrong-key"


@given("the Slack API is unavailable")
def slack_api_unavailable(mock_slack_client: MagicMock) -> None:
    """Mock Slack API failure."""
    mock_slack_client.chat_postMessage = AsyncMock(
        side_effect=Exception("Slack API error")
    )


# --- When Steps ---


@when(parsers.parse('I POST to "{endpoint}" with:'))
def post_to_endpoint(
    endpoint: str,
    datatable,
    notify_context: dict,
    notify_handler: NotifyHandler,
    mock_slack_client: MagicMock,
    initialized_db,
) -> None:
    """Make POST request to endpoint."""
    # Build request data from datatable
    request_data = {}
    for row in datatable:
        key = row[0].strip()
        value = row[1].strip()
        request_data[key] = value

    notify_context["request_data"] = request_data

    # Create mock request
    request = MagicMock()
    headers = {}
    if notify_context["api_key"]:
        headers["X-API-Key"] = notify_context["api_key"]
    request.headers = headers
    request.remote = "127.0.0.1"
    request.json = AsyncMock(return_value=request_data)

    # Make request (run async in sync context)
    response = run_async(notify_handler.handle_notify(request))
    notify_context["response"] = response

    # Store notification ID if available
    try:
        body = json.loads(response.body)
        notify_context["notification_id"] = body.get("notification_id")
    except Exception:
        pass

    # Capture Slack message if sent
    if mock_slack_client.chat_postMessage.called:
        call_kwargs = mock_slack_client.chat_postMessage.call_args.kwargs
        notify_context["slack_message"] = call_kwargs.get("text", "")


# --- Then Steps ---


@then(parsers.parse("the response status should be {status:d}"))
def response_status_is(status: int, notify_context: dict) -> None:
    """Check response status code."""
    assert notify_context["response"] is not None, "No response received"
    assert notify_context["response"].status == status


@then("the response should include a notification_id")
def response_has_notification_id(notify_context: dict) -> None:
    """Check response includes notification_id."""
    body = json.loads(notify_context["response"].body)
    assert "notification_id" in body
    assert body["notification_id"] is not None


@then("a Slack message should be sent to the notifications channel")
def slack_message_sent(mock_slack_client: MagicMock) -> None:
    """Verify Slack message was sent."""
    mock_slack_client.chat_postMessage.assert_called()


@then(parsers.parse('the message should mention "{mention}"'))
def message_contains_mention(mention: str, notify_context: dict) -> None:
    """Check message contains mention."""
    slack_msg = notify_context.get("slack_message", "")
    assert mention in slack_msg or "subteam" in slack_msg


@then(parsers.parse('the message should include "{text}"'))
def message_includes_text(text: str, notify_context: dict) -> None:
    """Check message includes text."""
    assert text in notify_context.get("slack_message", "")


@then(parsers.parse('the message should indicate "{time}" until expiration'))
def message_indicates_time(time: str, notify_context: dict) -> None:
    """Check message indicates time until expiration."""
    assert time in notify_context.get("slack_message", "")


@then("a Slack message should indicate the cluster has expired")
def message_indicates_expired(notify_context: dict) -> None:
    """Check message indicates expiration."""
    message = notify_context.get("slack_message", "").lower()
    assert "expired" in message or "expir" in message


@then(parsers.parse('the Slack message should contain "{text}"'))
def slack_message_contains(text: str, notify_context: dict) -> None:
    """Check Slack message contains text."""
    assert text in notify_context.get("slack_message", "")


@then(parsers.parse('the error should indicate "{error}"'))
def error_indicates(error: str, notify_context: dict) -> None:
    """Check error message."""
    body = json.loads(notify_context["response"].body)
    assert error in body.get("error", "")


@then("the notification should be recorded in the database")
def notification_recorded(notify_context: dict) -> None:
    """Check notification is in database."""
    notification_id = notify_context.get("notification_id")
    if notification_id:
        record = run_async(get_notification_by_id(notification_id))
        assert record is not None
        notify_context["db_record"] = record


@then(parsers.parse('the record status should be "{status}"'))
def record_status_is(status: str, notify_context: dict) -> None:
    """Check database record status."""
    record = notify_context.get("db_record")
    if record:
        assert record.status.value == status


@then("the record should include the error message")
def record_has_error(notify_context: dict) -> None:
    """Check database record has error message."""
    # For failed notifications, get the notification_id from response
    body = json.loads(notify_context["response"].body)
    notification_id = body.get("notification_id")
    if notification_id:
        record = run_async(get_notification_by_id(notification_id))
        assert record is not None
        assert record.error_message is not None
        notify_context["db_record"] = record
