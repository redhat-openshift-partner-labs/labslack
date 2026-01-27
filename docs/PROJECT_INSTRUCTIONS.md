# LabSlack Bot - Project Instructions

## Overview
A Slack bot that listens for messages (DMs and external webhooks) and relays them to a workspace-specific Slack channel.

## Key Requirements
- **Message Sources**: DMs to the bot, External webhooks
- **Workspace**: Single workspace deployment
- **Connection Mode**: HTTP endpoints (production-ready, aiohttp-based)
- **Message Format**: Configurable metadata (sender, timestamp, custom fields)

## Current Status
- **Core Features**: Complete and functional
- **DM Relay**: Working
- **Webhook Relay**: Working with API key authentication
- **Health Check**: Available at `/health`

## Development Approach
- **TDD**: Test-Driven Development - write tests first, then implementation
- **BDD**: Behavior-Driven Development - Gherkin feature files in `docs/features/`
- **Git**: Incremental commits with conventional commit messages

## Tech Stack
- Python 3.12+
- slack-bolt >= 1.27.0 (AsyncApp)
- aiohttp >= 3.13.3
- python-dotenv >= 1.0.0
- pytest + pytest-bdd + pytest-asyncio for testing

## Project Structure
```
labslack/
├── docs/                           # Documentation
│   ├── PROJECT_INSTRUCTIONS.md     # This file
│   ├── DEVELOPMENT_PLAN.md         # Phased development plan
│   ├── FEATURE_REQUEST_TEMPLATE.md # Template for new features
│   └── features/                   # BDD feature specifications
│       ├── dm_relay.feature
│       ├── webhook_relay.feature
│       └── message_formatting.feature
├── scripts/                        # Utility scripts
│   └── test_relay.py               # Manual testing script
├── src/labslack/                   # Source code
│   ├── __init__.py
│   ├── app.py                      # Main async Bolt app + aiohttp server
│   ├── config.py                   # Configuration from environment
│   ├── handlers/                   # Request handlers
│   │   ├── __init__.py
│   │   └── webhook_handler.py      # Webhook endpoint handler
│   ├── relay/                      # Message relay service
│   │   ├── __init__.py
│   │   └── message_relay.py        # Async relay to Slack channel
│   └── formatters/                 # Message formatting
│       ├── __init__.py
│       └── message_formatter.py    # Configurable message formatting
├── tests/                          # Test suite
│   ├── conftest.py                 # Shared fixtures
│   ├── unit/                       # Unit tests
│   │   ├── test_message_formatter.py
│   │   ├── test_dm_handler.py
│   │   └── test_webhook_handler.py
│   ├── integration/                # Integration tests
│   │   └── test_message_relay.py
│   └── bdd/                        # BDD step implementations
│       └── conftest.py
├── .env.example                    # Environment variable template
├── .gitignore
├── pyproject.toml                  # Project configuration
└── README.md                       # User-facing documentation
```

## Slack App Configuration

### 1. Create Slack App
1. Go to https://api.slack.com/apps
2. Click **Create New App** → **From scratch**
3. Name your app and select workspace

### 2. Configure Bot Token Scopes
Navigate to **OAuth & Permissions** → **Scopes** → **Bot Token Scopes**:
- `chat:write` - Send messages to channels
- `im:history` - Read DM message history
- `im:read` - View DM metadata

### 3. Enable Event Subscriptions
Navigate to **Event Subscriptions**:
1. Toggle **Enable Events** to On
2. Set **Request URL**: `https://your-domain/slack/events`
3. Under **Subscribe to bot events**, add: `message.im`
4. Save Changes

### 4. Install App
1. Go to **Install App**
2. Click **Install to Workspace**
3. Copy the **Bot User OAuth Token** (`xoxb-...`)

### 5. Get Signing Secret
1. Go to **Basic Information**
2. Under **App Credentials**, copy **Signing Secret**

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SLACK_BOT_TOKEN` | Yes | Bot token (`xoxb-...`) from OAuth & Permissions |
| `SLACK_SIGNING_SECRET` | Yes | Signing secret from Basic Information |
| `RELAY_CHANNEL_ID` | Yes* | Channel ID (`C...`) to relay messages to |
| `WEBHOOK_API_KEY` | No | API key for webhook authentication |
| `INCLUDE_METADATA` | No | Include sender/time metadata (default: `true`) |
| `HOST` | No | Server host (default: `0.0.0.0`) |
| `PORT` | No | Server port (default: `3000`) |
| `LOG_LEVEL` | No | Logging level (default: `INFO`) |

*Can be omitted for initial URL verification, but required for message relay.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/slack/events` | Slack event subscription endpoint |
| POST | `/webhook` | External webhook for message relay |
| GET | `/health` | Health check endpoint |

## Development Workflow
1. Check `docs/DEVELOPMENT_PLAN.md` for current phase
2. Write/update BDD feature file if adding new behavior
3. Write failing unit tests (Red)
4. Implement minimum code to pass (Green)
5. Refactor while keeping tests passing (Refactor)
6. Run full test suite: `uv run pytest`
7. Commit with conventional message
8. Update documentation if needed

## Git Commit Convention
```
feat: add new feature
fix: bug fix
test: add or update tests
docs: documentation changes
refactor: code refactoring
chore: maintenance tasks
```

## Git Policy
- **NEVER push to remote** - The user will handle all pushes manually
- **DO make frequent incremental commits** - Small, focused commits for easy rollback
- Use conventional commit messages
- Each commit should be atomic and self-contained

## Running the Bot

### Development (with ngrok)
```bash
# Terminal 1: Start the bot
uv run python -m labslack.app

# Terminal 2: Expose via ngrok
ngrok http 3000
```

### Testing
```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src/labslack

# Specific test file
uv run pytest tests/unit/test_message_formatter.py -v

# Manual testing
uv run python scripts/test_relay.py health
uv run python scripts/test_relay.py webhook "Test message"
uv run python scripts/test_relay.py dm "Direct test"
```

## Troubleshooting

### URL Verification Fails
- Ensure bot is running before configuring URL in Slack
- Check that signing secret matches
- Verify endpoint is `/slack/events` (not `/`)

### Messages Not Relaying
- Check `RELAY_CHANNEL_ID` is set correctly
- Ensure bot is invited to the relay channel
- Check bot logs for errors

### Webhook Returns 401
- Verify `X-API-Key` header matches `WEBHOOK_API_KEY`
- Ensure API key is set in environment
