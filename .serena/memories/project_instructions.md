# LabSlack Bot - Persistent Project Instructions

## Project Overview
A Slack bot that listens for messages (DMs and external webhooks) and relays them to a workspace-specific Slack channel.

## Requirements Summary
- **Message Sources**: DMs to the bot, External webhooks
- **Workspace**: Single workspace deployment
- **Connection Mode**: HTTP endpoints (production-ready)
- **Message Format**: Configurable metadata (sender, original channel, timestamp)

## Development Methodology
- **TDD**: Test-Driven Development - write tests first, then implementation
- **BDD**: Behavior-Driven Development - Gherkin feature files in `docs/features/`
- **Git**: Incremental commits for easy rollback

## Tech Stack
- Python 3.12+
- slack-bolt >= 1.27.0
- aiohttp >= 3.13.3
- pytest + pytest-bdd for testing

## Key Documentation Locations
- `docs/PROJECT_INSTRUCTIONS.md` - Full project instructions
- `docs/DEVELOPMENT_PLAN.md` - Phase-by-phase development plan
- `docs/features/*.feature` - BDD feature specifications

## Project Structure
```
src/labslack/
├── app.py              # Main Bolt app entry point
├── config.py           # Configuration from environment
├── handlers/           # DM and webhook handlers
├── relay/              # Message relay service
└── formatters/         # Message formatting
tests/
├── unit/               # Unit tests
├── integration/        # Integration tests
└── bdd/                # BDD step implementations
```

## Slack App Requirements
1. Enable Event Subscriptions at Request URL: `https://your-domain/slack/events`
2. Subscribe to bot events: `message.im`
3. Bot Token Scopes: `chat:write`, `im:history`, `im:read`, `channels:read`

## Environment Variables Required
- SLACK_BOT_TOKEN
- SLACK_SIGNING_SECRET
- RELAY_CHANNEL_ID
- INCLUDE_METADATA (optional, default: true)
- WEBHOOK_API_KEY
- HOST, PORT (optional)

## Commit Convention
- feat: new feature
- fix: bug fix
- test: tests
- docs: documentation
- refactor: refactoring
- chore: maintenance

## Development Workflow
1. Write BDD feature file
2. Write failing unit tests (Red)
3. Implement minimum code (Green)
4. Refactor (Refactor)
5. Commit with descriptive message
6. Repeat
