"""Main application entry point for LabSlack bot."""

from __future__ import annotations

import logging

from aiohttp import web
from dotenv import load_dotenv
from slack_bolt.adapter.aiohttp import to_aiohttp_response, to_bolt_request
from slack_bolt.async_app import AsyncApp

from labslack.config import Config
from labslack.database import close_database, init_database
from labslack.formatters.message_formatter import MessageFormatter
from labslack.handlers.notify_handler import NotifyHandler
from labslack.handlers.webhook_handler import WebhookHandler
from labslack.logging import configure_logging, get_logger
from labslack.metrics import get_metrics
from labslack.notifications import NotificationService
from labslack.relay.message_relay import MessageRelay


def create_app(config: Config | None = None) -> tuple[AsyncApp, web.Application]:
    """Create and configure the Slack Bolt app and aiohttp app."""
    if config is None:
        load_dotenv()
        config = Config.from_env()

    # Configure structured logging
    configure_logging(level=config.log_level, json_format=config.log_json)
    logger = get_logger("app")

    # Initialize metrics
    metrics = get_metrics()
    dm_counter = metrics.counter("messages_received_total", "Total messages received")
    relay_latency = metrics.histogram("relay_latency_seconds", "Relay operation latency")

    # Create async Bolt app
    bolt_app = AsyncApp(
        token=config.slack_bot_token,
        signing_secret=config.slack_signing_secret,
    )

    # Create services
    formatter = MessageFormatter(config)
    relay = MessageRelay(config, bolt_app.client, formatter)

    # Register DM handler
    @bolt_app.event("message")
    async def handle_message(event: dict, say, client) -> None:
        """Handle incoming DM messages."""
        # Skip bot messages and message subtypes
        if event.get("bot_id") or event.get("subtype"):
            return

        # Only handle DMs (channel_type == "im")
        if event.get("channel_type") != "im":
            return

        text = event.get("text", "").strip()
        if not text:
            return

        user_id = event.get("user")
        timestamp = event.get("ts")

        dm_counter.labels(source="dm").inc()
        logger.info(
            "Received DM",
            extra={"user_id": user_id, "text_preview": text[:50], "source": "dm"},
        )

        if config.relay_channel_id:
            with relay_latency.labels(source="dm").time():
                await relay.relay_dm(
                    text=text,
                    user_id=user_id,
                    timestamp=timestamp,
                )
        else:
            logger.warning(
                "Cannot relay - RELAY_CHANNEL_ID not configured",
                extra={"user_id": user_id},
            )

    # Create webhook handler and aiohttp app
    webhook_handler = WebhookHandler(config, relay)
    aiohttp_app = web.Application()
    aiohttp_app.add_routes(webhook_handler.get_routes())

    # Create notification service and handler
    notification_service = NotificationService(config, bolt_app.client)
    notify_handler = NotifyHandler(config, notification_service)
    aiohttp_app.add_routes(notify_handler.get_routes())

    # Store config for startup/cleanup handlers
    aiohttp_app["config"] = config

    async def on_startup(app: web.Application) -> None:
        """Initialize database on startup."""
        await init_database(app["config"])
        logger.info("Database initialized", extra={"path": app["config"].database_path})

    async def on_cleanup(app: web.Application) -> None:
        """Close database on shutdown."""
        await close_database()
        logger.info("Database connection closed")

    aiohttp_app.on_startup.append(on_startup)
    aiohttp_app.on_cleanup.append(on_cleanup)

    # Create Slack events handler for aiohttp
    async def handle_slack_events(request: web.Request) -> web.Response:
        """Handle Slack events via aiohttp."""
        bolt_request = await to_bolt_request(request)
        bolt_response = await bolt_app.async_dispatch(bolt_request)
        return await to_aiohttp_response(bolt_response)

    aiohttp_app.router.add_post("/slack/events", handle_slack_events)

    logger.info("LabSlack bot initialized", extra={"host": config.host, "port": config.port})

    return bolt_app, aiohttp_app


def main() -> None:
    """Run the application."""
    load_dotenv()

    # Initial basic logging until config is loaded
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    init_logger = logging.getLogger(__name__)

    try:
        config = Config.from_env()
    except KeyError as e:
        init_logger.error(f"Missing required environment variable: {e}")
        init_logger.error("Required: SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET")
        init_logger.error("Optional: RELAY_CHANNEL_ID, WEBHOOK_API_KEY")
        raise SystemExit(1)

    bolt_app, aiohttp_app = create_app(config)

    # Use structured logger after create_app configures logging
    logger = get_logger("app")
    logger.info(
        "Starting LabSlack bot",
        extra={
            "host": config.host,
            "port": config.port,
            "log_json": config.log_json,
        },
    )
    logger.info(
        "Endpoints available",
        extra={
            "slack_events": f"http://{config.host}:{config.port}/slack/events",
            "webhook": f"http://{config.host}:{config.port}/webhook",
            "notify": f"http://{config.host}:{config.port}/api/notify",
            "health": f"http://{config.host}:{config.port}/health",
            "metrics": f"http://{config.host}:{config.port}/metrics",
        },
    )

    if not config.relay_channel_id:
        logger.warning(
            "RELAY_CHANNEL_ID not set - bot will start but cannot relay messages"
        )

    # Run aiohttp server
    web.run_app(aiohttp_app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
