# LabSlack

A Slack bot that listens for direct messages and external webhooks, then relays them to a designated Slack channel.

## Features

- **DM Relay**: Messages sent directly to the bot are forwarded to a configured channel
- **Webhook Relay**: External systems can send messages via HTTP webhook
- **Configurable Metadata**: Include or exclude sender info, timestamps, and custom fields
- **Production Ready**: Uses HTTP endpoints suitable for deployment

## Installation

```bash
uv sync --all-extras
```

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Description |
|----------|-------------|
| `SLACK_BOT_TOKEN` | Bot token from Slack App (starts with `xoxb-`) |
| `SLACK_SIGNING_SECRET` | Signing secret from Slack App Basic Info |
| `RELAY_CHANNEL_ID` | Channel ID to relay messages to (starts with `C`) |
| `WEBHOOK_API_KEY` | API key for authenticating webhook requests |

## Slack App Setup

1. Create app at https://api.slack.com/apps
2. Add Bot Token Scopes: `chat:write`, `im:history`, `im:read`
3. Enable Event Subscriptions with URL: `https://your-domain/slack/events`
4. Subscribe to bot events: `message.im`
5. Install to workspace

## Usage

```bash
# Run the bot
uv run python -m labslack.app

# Or after installing
labslack
```

## Development

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

## License

MIT
