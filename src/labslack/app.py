"""Main application entry point for LabSlack bot."""

from __future__ import annotations

import logging

from aiohttp import web
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from labslack.config import Config
from labslack.formatters.message_formatter import MessageFormatter
from labslack.handlers.dm_handler import DMHandler
from labslack.handlers.webhook_handler import WebhookHandler
from labslack.relay.message_relay import MessageRelay


def create_app(config: Config | None = None) -> tuple[App, web.Application]:
    """Create and configure the Slack Bolt app and aiohttp app."""
    if config is None:
        load_dotenv()
        config = Config.from_env()

    # Configure logging
    logging.basicConfig(level=getattr(logging, config.log_level))
    logger = logging.getLogger(__name__)

    # Create Bolt app
    bolt_app = App(
        token=config.slack_bot_token,
        signing_secret=config.slack_signing_secret,
    )

    # Create services
    formatter = MessageFormatter(config)
    relay = MessageRelay(config, bolt_app.client, formatter)

    # Register DM handler
    dm_handler = DMHandler(config, relay)
    dm_handler.register(bolt_app)

    # Create webhook handler and aiohttp app
    webhook_handler = WebhookHandler(config, relay)
    aiohttp_app = web.Application()
    aiohttp_app.add_routes(webhook_handler.get_routes())

    # Add Bolt's request handler
    from slack_bolt.adapter.aiohttp import SlackRequestHandler

    handler = SlackRequestHandler(bolt_app)
    aiohttp_app.router.add_post("/slack/events", handler.handle)

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
