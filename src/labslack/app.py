"""Main application entry point for LabSlack bot."""

from __future__ import annotations

import logging

from aiohttp import web
from dotenv import load_dotenv
from slack_bolt.adapter.aiohttp import to_bolt_request, to_aiohttp_response
from slack_bolt.async_app import AsyncApp

from labslack.config import Config
from labslack.formatters.message_formatter import MessageFormatter
from labslack.handlers.webhook_handler import WebhookHandler
from labslack.relay.message_relay import MessageRelay


def create_app(config: Config | None = None) -> tuple[AsyncApp, web.Application]:
    """Create and configure the Slack Bolt app and aiohttp app."""
    if config is None:
        load_dotenv()
        config = Config.from_env()

    # Configure logging
    logging.basicConfig(level=getattr(logging, config.log_level))
    logger = logging.getLogger(__name__)

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

        logger.info(f"Received DM from {user_id}: {text[:50]}...")

        if config.relay_channel_id:
            relay.relay_dm(
                text=text,
                user_id=user_id,
                timestamp=timestamp,
            )
        else:
            logger.warning("Cannot relay - RELAY_CHANNEL_ID not configured")

    # Create webhook handler and aiohttp app
    webhook_handler = WebhookHandler(config, relay)
    aiohttp_app = web.Application()
    aiohttp_app.add_routes(webhook_handler.get_routes())

    # Create Slack events handler for aiohttp
    async def handle_slack_events(request: web.Request) -> web.Response:
        """Handle Slack events via aiohttp."""
        bolt_request = await to_bolt_request(request)
        bolt_response = await bolt_app.async_dispatch(bolt_request)
        return to_aiohttp_response(bolt_response)

    aiohttp_app.router.add_post("/slack/events", handle_slack_events)

    logger.info("LabSlack bot initialized")

    return bolt_app, aiohttp_app


def main() -> None:
    """Run the application."""
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        config = Config.from_env()
    except KeyError as e:
        logger.error(f"Missing required environment variable: {e}")
        logger.error("Required: SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET")
        logger.error("Optional: RELAY_CHANNEL_ID, WEBHOOK_API_KEY")
        raise SystemExit(1)

    bolt_app, aiohttp_app = create_app(config)

    logger.info(f"Starting LabSlack bot on {config.host}:{config.port}")
    logger.info(f"Slack events endpoint: http://{config.host}:{config.port}/slack/events")
    logger.info(f"Webhook endpoint: http://{config.host}:{config.port}/webhook")
    logger.info(f"Health check: http://{config.host}:{config.port}/health")

    if not config.relay_channel_id:
        logger.warning("RELAY_CHANNEL_ID not set - bot will start but cannot relay messages")

    # Run aiohttp server
    web.run_app(aiohttp_app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
