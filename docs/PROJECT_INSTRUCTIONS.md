# LabSlack Bot - Project Instructions

## Overview
A Slack bot that listens for messages (DMs and external webhooks) and relays them to a workspace-specific Slack channel.

## Key Requirements
- **Message Sources**: DMs to the bot, External webhooks
- **Workspace**: Single workspace deployment
- **Connection Mode**: HTTP endpoints (production-ready)
- **Message Format**: Configurable metadata (sender, original channel, timestamp)

## Development Approach
- **TDD**: Test-Driven Development - write tests first, then implementation
- **BDD**: Behavior-Driven Development - use Gherkin syntax for feature specifications
- **Git**: Incremental commits for easy rollback

## Tech Stack
- Python 3.12+
- slack-bolt >= 1.27.0
- aiohttp >= 3.13.3
- pytest + pytest-bdd for testing
- pytest-asyncio for async tests

## Project Structure
```
labslack/
├── docs/                    # Documentation and plans
│   ├── PROJECT_INSTRUCTIONS.md
│   ├── DEVELOPMENT_PLAN.md
│   └── features/            # BDD feature files
│       ├── dm_relay.feature
│       └── webhook_relay.feature
├── src/
│   └── labslack/
│       ├── __init__.py
│       ├── app.py           # Main Bolt app
│       ├── config.py        # Configuration management
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── dm_handler.py
│       │   └── webhook_handler.py
│       ├── relay/
│       │   ├── __init__.py
│       │   └── message_relay.py
│       └── formatters/
│           ├── __init__.py
│           └── message_formatter.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_message_formatter.py
│   │   ├── test_dm_handler.py
│   │   └── test_webhook_handler.py
│   ├── integration/
│   │   └── test_message_relay.py
│   └── bdd/
│       ├── conftest.py
│       ├── test_dm_relay.py
│       └── test_webhook_relay.py
├── pyproject.toml
└── README.md
```

## Slack App Configuration Required
1. Create Slack App at https://api.slack.com/apps
2. Enable Event Subscriptions with Request URL
3. Subscribe to bot events: `message.im`
4. Add Bot Token Scopes:
   - `chat:write` - Send messages
   - `im:history` - Read DM history
   - `im:read` - View DM metadata
   - `channels:read` - View channel info
5. Install app to workspace
6. Note: Bot Token (`xoxb-`) and Signing Secret

## Environment Variables
```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
RELAY_CHANNEL_ID=C0123456789
INCLUDE_METADATA=true
PORT=3000
```

## Development Workflow
1. Write BDD feature file describing behavior
2. Write failing unit tests (Red)
3. Implement minimum code to pass (Green)
4. Refactor while keeping tests passing (Refactor)
5. Commit with descriptive message
6. Repeat

## Git Commit Convention
```
feat: add new feature
fix: bug fix
test: add or update tests
docs: documentation changes
refactor: code refactoring
chore: maintenance tasks
```
