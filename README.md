# LabSlack

A Slack bot that listens for direct messages and external webhooks, then relays them to a designated Slack channel.

## Features

- **DM Relay**: Messages sent directly to the bot are forwarded to a configured channel
- **Webhook Relay**: External systems can send messages via authenticated HTTP webhook
- **Configurable Metadata**: Include or exclude sender info, timestamps, and custom fields
- **Health Check**: Built-in `/health` endpoint for monitoring
- **Error Handling**: Automatic retry with exponential backoff for Slack API errors
- **Production Ready**: Async architecture with aiohttp, suitable for deployment

## Quick Start

### 1. Install Dependencies

```bash
uv sync --all-extras
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Slack credentials
```

### 3. Set Up Slack App

1. Create app at https://api.slack.com/apps
2. Add Bot Token Scopes: `chat:write`, `im:history`, `im:read`
3. Install to workspace and copy Bot Token
4. Copy Signing Secret from Basic Information

### 4. Run the Bot

```bash
# Start the bot
uv run python -m labslack.app

# In another terminal, expose via ngrok (for development)
ngrok http 3000
```

### 5. Configure Event Subscriptions

1. In Slack App settings, go to **Event Subscriptions**
2. Enable Events and set Request URL: `https://your-ngrok-url/slack/events`
3. Subscribe to bot events: `message.im`
4. Save Changes

### 6. Test It

- Send a DM to your bot in Slack
- The message should appear in your relay channel

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_BOT_TOKEN` | Yes | - | Bot token (`xoxb-...`) |
| `SLACK_SIGNING_SECRET` | Yes | - | Signing secret from Basic Info |
| `RELAY_CHANNEL_ID` | Yes | - | Channel ID (`C...`) for relayed messages |
| `WEBHOOK_API_KEY` | No | - | API key for webhook authentication |
| `INCLUDE_METADATA` | No | `true` | Include sender/timestamp in relayed messages |
| `HOST` | No | `0.0.0.0` | Server bind address |
| `PORT` | No | `3000` | Server port |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `MAX_RETRIES` | No | `3` | Max retry attempts for Slack API errors |
| `RETRY_BASE_DELAY` | No | `1.0` | Base delay (seconds) for exponential backoff |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/slack/events` | Slack Signature | Slack event subscription endpoint |
| POST | `/webhook` | `X-API-Key` header | External webhook for message relay |
| GET | `/health` | None | Health check (returns `{"status": "healthy"}`) |

## Webhook Usage

Send messages from external systems:

```bash
curl -X POST https://your-domain/webhook \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"message": "Deploy completed!", "source": "CI/CD"}'
```

## Development

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src/labslack --cov-report=html

# Specific test file
uv run pytest tests/unit/test_message_formatter.py -v
```

### Manual Testing

```bash
# Test health endpoint
uv run python scripts/test_relay.py health

# Test webhook (requires WEBHOOK_API_KEY in .env)
uv run python scripts/test_relay.py webhook "Hello from test!"

# Test direct Slack message (requires SLACK_BOT_TOKEN and RELAY_CHANNEL_ID)
uv run python scripts/test_relay.py dm "Test message"
```

### Code Quality

```bash
# Linting
uv run ruff check src/

# Type checking
uv run mypy src/

# Format check
uv run ruff format --check src/
```

## Project Structure

```
labslack/
├── docs/                    # Documentation
│   ├── PROJECT_INSTRUCTIONS.md
│   ├── DEVELOPMENT_PLAN.md
│   ├── FEATURE_REQUEST_TEMPLATE.md
│   └── features/            # BDD feature specifications
├── scripts/                 # Utility scripts
│   └── test_relay.py
├── src/labslack/           # Source code
│   ├── app.py              # Main application
│   ├── config.py           # Configuration
│   ├── handlers/           # Request handlers
│   ├── relay/              # Message relay service
│   └── formatters/         # Message formatting
└── tests/                  # Test suite
    ├── unit/
    ├── integration/
    └── bdd/
```

## Documentation

- [Project Instructions](docs/PROJECT_INSTRUCTIONS.md) - Detailed setup and development guide
- [Development Plan](docs/DEVELOPMENT_PLAN.md) - Phased development roadmap
- [Architecture](docs/ARCHITECTURE.md) - System architecture diagrams
- [Feature Request Template](docs/FEATURE_REQUEST_TEMPLATE.md) - Template for proposing new features
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project

## Contributing

1. Check `docs/DEVELOPMENT_PLAN.md` for current priorities
2. Use `docs/FEATURE_REQUEST_TEMPLATE.md` for new feature proposals
3. Follow TDD: write tests first
4. Use conventional commits: `feat:`, `fix:`, `test:`, `docs:`
5. Run tests before committing: `uv run pytest`

## Troubleshooting

### URL Verification Fails
- Ensure bot is running **before** configuring URL in Slack
- Verify signing secret matches exactly
- Endpoint must be `/slack/events` (not `/`)

### Messages Not Relaying
- Check `RELAY_CHANNEL_ID` is correct (starts with `C`)
- Invite bot to the relay channel: `/invite @YourBotName`
- Check bot logs for errors

### Webhook Returns 401
- Include `X-API-Key` header in request
- Verify key matches `WEBHOOK_API_KEY` environment variable

### Bot Not Receiving DMs
- Verify `message.im` event is subscribed in Slack App settings
- Check that Event Subscriptions URL is verified
- Ensure bot has `im:history` and `im:read` scopes

### Messages Failing to Relay (Slack API Errors)
- Check bot logs for error messages
- **rate_limited**: Bot will automatically retry with backoff; reduce message volume
- **channel_not_found**: Verify `RELAY_CHANNEL_ID` is correct
- **not_in_channel**: Invite bot to the channel: `/invite @YourBotName`
- **invalid_auth**: Check `SLACK_BOT_TOKEN` is valid and not revoked
- Adjust `MAX_RETRIES` and `RETRY_BASE_DELAY` if needed

## License

MIT
