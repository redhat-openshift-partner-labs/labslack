# LabSlack Bot - Persistent Project Instructions

## Project Overview
A Slack bot that listens for messages (DMs and external webhooks) and relays them to a workspace-specific Slack channel.

## Current Status: Core Features Complete
- DM Relay: Working
- Webhook Relay: Working with API key auth
- Health Check: Available at `/health`
- Error Handling: Automatic retry with exponential backoff
- All async with aiohttp

## Requirements Summary
- **Message Sources**: DMs to the bot, External webhooks
- **Workspace**: Single workspace deployment
- **Connection Mode**: HTTP endpoints (aiohttp + AsyncApp)
- **Message Format**: Configurable metadata

## Development Methodology
- **TDD**: Test-Driven Development
- **BDD**: Gherkin feature files in `docs/features/`
- **Git**: Conventional commits, incremental changes

## Tech Stack
- Python 3.12+
- slack-bolt >= 1.27.0 (AsyncApp)
- aiohttp >= 3.13.3
- pytest + pytest-bdd + pytest-asyncio

## Key Documentation
- `docs/PROJECT_INSTRUCTIONS.md` - Full setup guide
- `docs/DEVELOPMENT_PLAN.md` - Phased roadmap with status
- `docs/FEATURE_REQUEST_TEMPLATE.md` - New feature proposals
- `docs/features/*.feature` - BDD specifications
- `README.md` - User-facing quick start

## Project Structure
```
src/labslack/
├── app.py              # Main AsyncApp + aiohttp server
├── config.py           # Configuration from environment
├── logging.py          # Structured JSON logging
├── metrics.py          # Observability metrics (Counter, Gauge, Histogram)
├── handlers/           # Webhook handler
├── relay/              # Async message relay
└── formatters/         # Message formatting
scripts/
└── test_relay.py       # Manual testing
tests/
├── unit/               # Unit tests
├── integration/        # Integration tests
└── bdd/                # BDD fixtures
```

## Environment Variables
- SLACK_BOT_TOKEN (required)
- SLACK_SIGNING_SECRET (required)
- RELAY_CHANNEL_ID (required for relay)
- WEBHOOK_API_KEY (optional)
- INCLUDE_METADATA (default: true)
- HOST, PORT, LOG_LEVEL (optional)
- LOG_JSON (default: true, set to false for human-readable logs)
- MAX_RETRIES, RETRY_BASE_DELAY (optional, for error retry)

## API Endpoints
- POST /slack/events - Slack events
- POST /webhook - External messages
- GET /health - Health check
- GET /metrics - Observability metrics (JSON)

## Development Phases
- Phases 1-6: Complete (setup, formatter, handlers, relay with error handling, integration, structured logging, metrics)
- Phase 7: In Progress (documentation)
- Phase 8-10: Planned (hardening, deployment, enhanced features)

## Error Handling (Phase 5 Complete)
- Retryable errors: rate_limited, service_unavailable, request_timeout, internal_error
- Non-retryable errors: channel_not_found, invalid_auth, not_in_channel, etc.
- Exponential backoff with configurable base delay
- Respects Retry-After header for rate limiting