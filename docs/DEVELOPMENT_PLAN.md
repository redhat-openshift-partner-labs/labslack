# LabSlack Bot - Development Plan

## Overview
This document tracks the phased development of the LabSlack bot, following TDD/BDD practices.

---

## Phase 1: Project Setup & Foundation [COMPLETED]
**Status**: Done

### Completed Tasks:
- [x] Set up project structure with src layout
- [x] Configure pyproject.toml with all dependencies
- [x] Create pytest configuration with async support
- [x] Set up BDD test infrastructure with pytest-bdd
- [x] Create configuration module with environment variable handling
- [x] Initial git commit

### Deliverables:
- Working project skeleton
- Test infrastructure ready
- Configuration management via `Config` dataclass

---

## Phase 2: Message Formatter [COMPLETED]
**Status**: Done

### Completed Tasks:
- [x] Write BDD feature file (`docs/features/message_formatting.feature`)
- [x] Write unit tests (`tests/unit/test_message_formatter.py`)
- [x] Implement `MessageFormatter` with configurable metadata
- [x] Support for DM and webhook message formatting
- [x] Message truncation for Slack limits

### Key Features:
- Configurable metadata inclusion via `INCLUDE_METADATA`
- User mention formatting (`<@USER_ID>`)
- Timestamp parsing and formatting
- Custom field support for webhooks

---

## Phase 3: DM Handler [COMPLETED]
**Status**: Done

### Completed Tasks:
- [x] Write BDD feature file (`docs/features/dm_relay.feature`)
- [x] Write unit tests (`tests/unit/test_dm_handler.py`)
- [x] Implement DM handling in main app (inline async handler)
- [x] Filter out bot messages and subtypes
- [x] Filter to only process `im` channel types

### Key Features:
- Async event handler registered on `AsyncApp`
- Ignores bot's own messages
- Ignores message subtypes (edits, deletes, etc.)
- Only processes direct messages (channel_type == "im")

---

## Phase 4: Webhook Handler [COMPLETED]
**Status**: Done

### Completed Tasks:
- [x] Write BDD feature file (`docs/features/webhook_relay.feature`)
- [x] Write unit tests (`tests/unit/test_webhook_handler.py`)
- [x] Implement webhook endpoint with aiohttp
- [x] Add API key authentication via `X-API-Key` header
- [x] Input validation (required message, non-empty)
- [x] Health check endpoint

### Key Features:
- POST `/webhook` for external message ingestion
- API key authentication
- JSON payload validation
- Custom metadata pass-through
- GET `/health` for monitoring

---

## Phase 5: Message Relay Service [COMPLETED]
**Status**: Done

### Completed Tasks:
- [x] Implement async `MessageRelay` service
- [x] Integration with `AsyncWebClient`
- [x] Support for both DM and webhook relay

### Remaining Tasks:
- [ ] Add error handling for Slack API failures
- [ ] Add retry logic with exponential backoff
- [ ] Add logging for relay success/failure

---

## Phase 6: Application Integration [COMPLETED]
**Status**: Done

### Completed Tasks:
- [x] Create main `AsyncApp` application in `app.py`
- [x] Wire up all handlers and services
- [x] Add health check endpoint
- [x] Write integration tests
- [x] Manual test script (`scripts/test_relay.py`)

### Remaining Tasks:
- [ ] Add structured logging
- [ ] Add metrics/observability hooks

---

## Phase 7: Documentation [IN PROGRESS]
**Status**: In Progress

### Completed Tasks:
- [x] Write README.md
- [x] Create .env.example
- [x] Write PROJECT_INSTRUCTIONS.md
- [x] Create BDD feature files

### Current Tasks:
- [x] Update all documentation to reflect current state
- [x] Create feature request template
- [ ] Add CONTRIBUTING.md
- [ ] Add architecture diagram

---

## Phase 8: Production Hardening [PLANNED]
**Status**: Not Started

### Tasks:
1. [ ] Add comprehensive error handling
2. [ ] Implement retry logic for Slack API calls
3. [ ] Add rate limiting for webhook endpoint
4. [ ] Add request ID tracking for debugging
5. [ ] Add structured JSON logging
6. [ ] Security audit (input sanitization, etc.)

### Acceptance Criteria:
- Bot recovers gracefully from Slack API errors
- Webhook endpoint handles high load
- All errors are logged with context

---

## Phase 9: Deployment [PLANNED]
**Status**: Not Started

### Tasks:
1. [ ] Create Dockerfile
2. [ ] Create docker-compose.yml for local testing
3. [ ] Add Kubernetes manifests (optional)
4. [ ] Add systemd service file (optional)
5. [ ] Document deployment procedures
6. [ ] Add CI/CD pipeline configuration

### Acceptance Criteria:
- One-command deployment
- Health checks for orchestration
- Graceful shutdown handling

---

## Phase 10: Enhanced Features [PLANNED]
**Status**: Not Started

### Potential Features:
1. [ ] Message filtering (keywords, regex)
2. [ ] User allowlist/blocklist
3. [ ] Multiple relay channels based on rules
4. [ ] Message threading support
5. [ ] Reaction/emoji support
6. [ ] File attachment handling
7. [ ] Slack command support (`/relay`)
8. [ ] Admin commands for configuration

---

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock Slack API calls with `MagicMock`/`AsyncMock`
- Test all edge cases and error conditions
- Location: `tests/unit/`

### Integration Tests
- Test component interactions
- Use aiohttp test client
- Verify end-to-end message flow
- Location: `tests/integration/`

### BDD Tests
- Feature-level acceptance tests
- Human-readable Gherkin specifications
- Stakeholder communication tool
- Location: `tests/bdd/` + `docs/features/`

### Manual Testing
- Use `scripts/test_relay.py` for quick verification
- Test with real Slack workspace for final validation

---

## Definition of Done

A task/feature is complete when:
- [ ] All related tests pass (unit, integration)
- [ ] Code follows project style (ruff, mypy)
- [ ] No regressions in existing functionality
- [ ] Feature is documented (code comments, README if user-facing)
- [ ] Committed with conventional commit message
- [ ] Reviewed (if team project)

---

## Backlog

Ideas and requests not yet scheduled:

| ID | Description | Priority | Effort |
|----|-------------|----------|--------|
| B1 | Socket Mode support for firewalled envs | Medium | Medium |
| B2 | Multi-workspace support (OAuth) | Low | High |
| B3 | Web dashboard for configuration | Low | High |
| B4 | Slack Block Kit message formatting | Medium | Medium |
| B5 | Database for message history | Low | Medium |
