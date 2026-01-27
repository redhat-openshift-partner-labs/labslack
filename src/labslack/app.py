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
    config = Config.from_env()

    bolt_app, aiohttp_app = create_app(config)

    # Run aiohttp server
    web.run_app(aiohttp_app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
