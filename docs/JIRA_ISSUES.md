# LabSlack Bot - Jira Issue Notes

This document contains detailed notes for generating Jira issues based on completed and planned work.

---

## Epic: LABSLACK - LabSlack Slack Relay Bot

**Summary**: Develop a Slack bot that relays direct messages and external webhook messages to a designated Slack channel

**Description**:
LabSlack is a production-ready Slack bot that enables message relay from two sources:
1. Direct Messages (DMs) sent to the bot by Slack users
2. External webhook messages from CI/CD pipelines, monitoring systems, and other integrations

The bot is built with an async-first architecture using Python 3.12+, slack-bolt (AsyncApp), and aiohttp. It follows TDD/BDD development practices with comprehensive test coverage.

**Components**:
- Message Formatter (configurable metadata)
- DM Handler (Slack event processing)
- Webhook Handler (REST API with authentication)
- Message Relay Service (with error handling and retry logic)
- Observability (structured logging, metrics)

**Labels**: `slack`, `bot`, `python`, `async`, `relay`

---

# Completed Work (Historical Reference)

## Story: LABSLACK-1 - Project Setup & Foundation

**Type**: Story
**Status**: Done
**Priority**: High
**Sprint**: Phase 1

**Summary**: Set up project structure and development infrastructure

**Description**:
Establish the foundational project structure, configuration management, and testing infrastructure for the LabSlack bot.

**Acceptance Criteria**:
- [x] Project uses src layout (`src/labslack/`)
- [x] `pyproject.toml` configured with all dependencies
- [x] pytest configured with async support (`pytest-asyncio`)
- [x] BDD test infrastructure with `pytest-bdd`
- [x] Configuration module loads from environment variables
- [x] `.env.example` template provided
- [x] Initial git repository with conventional commits

**Technical Details**:
- Python 3.12+ required
- Dependencies: slack-bolt>=1.27.0, aiohttp>=3.13.3, python-dotenv>=1.0.0
- Dev dependencies: pytest, pytest-bdd, pytest-asyncio, ruff, mypy

**Files Created**:
- `src/labslack/__init__.py`
- `src/labslack/config.py`
- `pyproject.toml`
- `tests/conftest.py`
- `.env.example`
- `.gitignore`

---

## Story: LABSLACK-2 - Message Formatter Component

**Type**: Story
**Status**: Done
**Priority**: High
**Sprint**: Phase 2

**Summary**: Implement configurable message formatting for relay

**Description**:
Create a `MessageFormatter` class that formats messages for relay with configurable metadata inclusion. Supports both DM and webhook message types with different formatting requirements.

**User Story**:
```
As a relay bot
I want to format messages with configurable metadata
So that recipients understand the message context
```

**Acceptance Criteria**:
- [x] Format DM messages with user mention (`<@USER_ID>`)
- [x] Format DM messages with timestamp
- [x] Format webhook messages with source identifier
- [x] Support custom metadata fields for webhooks
- [x] Toggle metadata via `INCLUDE_METADATA` env var
- [x] Truncate messages exceeding 4000 characters
- [x] Handle empty/edge case messages gracefully
- [x] BDD feature file created
- [x] Unit tests with 100% coverage

**Technical Details**:
- Location: `src/labslack/formatters/message_formatter.py`
- Slack message limit: 4000 characters
- User mentions format: `<@U12345678>`
- Timestamp parsing from Slack epoch format

**Test Scenarios**:
1. Format DM with full metadata
2. Format DM without metadata
3. Format webhook with source
4. Format webhook with custom fields
5. Escape special Slack characters
6. Truncate long messages
7. Handle attachment references

**Files**:
- `src/labslack/formatters/__init__.py`
- `src/labslack/formatters/message_formatter.py`
- `tests/unit/test_message_formatter.py`
- `docs/features/message_formatting.feature`

---

## Story: LABSLACK-3 - DM Handler Component

**Type**: Story
**Status**: Done
**Priority**: High
**Sprint**: Phase 3

**Summary**: Implement direct message event handling

**Description**:
Create an async event handler that processes `message.im` events from Slack, filters inappropriate messages, and forwards valid DMs for relay.

**User Story**:
```
As a Slack user
I want to send direct messages to the bot
So that my message is relayed to the designated channel
```

**Acceptance Criteria**:
- [x] Async event handler for `message.im` events
- [x] Filter out messages from the bot itself
- [x] Filter out message subtypes (edits, deletes, reactions)
- [x] Only process `channel_type == "im"`
- [x] Extract user ID, text, and timestamp
- [x] Handle empty messages gracefully
- [x] BDD feature file created
- [x] Unit tests with mocked Slack client

**Technical Details**:
- Handler registered on `AsyncApp.event("message")`
- Filter logic: `subtype is None AND bot_id is None AND channel_type == "im"`
- Event payload fields: `user`, `text`, `ts`, `channel_type`, `channel`

**Test Scenarios**:
1. Successfully relay a DM
2. Relay with metadata enabled
3. Relay with metadata disabled
4. Ignore bot's own messages
5. Ignore message subtypes
6. Handle empty message

**Files**:
- `src/labslack/app.py` (inline handler)
- `tests/unit/test_dm_handler.py`
- `docs/features/dm_relay.feature`

---

## Story: LABSLACK-4 - Webhook Handler Component

**Type**: Story
**Status**: Done
**Priority**: High
**Sprint**: Phase 4

**Summary**: Implement REST webhook endpoint for external message ingestion

**Description**:
Create an aiohttp-based webhook endpoint that accepts authenticated POST requests from external systems and forwards messages for relay.

**User Story**:
```
As an external system
I want to send messages via webhook to the Slack bot
So that they are relayed to the designated Slack channel
```

**Acceptance Criteria**:
- [x] POST `/webhook` endpoint for message ingestion
- [x] API key authentication via `X-API-Key` header
- [x] Return 401 for missing/invalid API key
- [x] Return 400 for missing `message` field
- [x] Return 400 for empty message
- [x] Return 400 for malformed JSON
- [x] Return 200 with success response
- [x] Support custom metadata fields
- [x] GET `/health` endpoint for monitoring
- [x] BDD feature file created
- [x] Unit tests with aiohttp test client

**Technical Details**:
- Location: `src/labslack/handlers/webhook_handler.py`
- Authentication: `X-API-Key` header compared to `WEBHOOK_API_KEY` env var
- Payload schema: `{ "message": string (required), "source": string, ...custom_fields }`
- Health response: `{ "status": "healthy" }`

**API Endpoints**:
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/webhook` | X-API-Key | Message ingestion |
| GET | `/health` | None | Health check |

**Test Scenarios**:
1. Successfully relay webhook message
2. Relay with custom metadata
3. Reject missing API key (401)
4. Reject invalid API key (401)
5. Reject missing message field (400)
6. Reject empty message (400)
7. Handle malformed JSON (400)
8. Health check returns healthy

**Files**:
- `src/labslack/handlers/__init__.py`
- `src/labslack/handlers/webhook_handler.py`
- `tests/unit/test_webhook_handler.py`
- `docs/features/webhook_relay.feature`

---

## Story: LABSLACK-5 - Message Relay Service

**Type**: Story
**Status**: Done
**Priority**: High
**Sprint**: Phase 5

**Summary**: Implement async message relay with error handling and retry logic

**Description**:
Create a `MessageRelay` service that sends formatted messages to Slack's API with comprehensive error handling, automatic retry for transient errors, and exponential backoff.

**User Story**:
```
As the relay bot
I want to send messages to Slack with automatic retry
So that transient errors don't cause message loss
```

**Acceptance Criteria**:
- [x] Async `relay_message()` method using `AsyncWebClient`
- [x] Call `chat.postMessage` with formatted content
- [x] Categorize Slack API errors (retryable vs non-retryable)
- [x] Implement exponential backoff for retries
- [x] Respect `Retry-After` header for rate limiting
- [x] Configurable `MAX_RETRIES` (default: 3)
- [x] Configurable `RETRY_BASE_DELAY` (default: 1.0s)
- [x] Log all relay attempts at appropriate levels
- [x] Return success/failure status
- [x] Unit tests with mocked Slack client
- [x] Integration tests for retry behavior

**Technical Details**:
- Location: `src/labslack/relay/message_relay.py`
- Backoff formula: `base_delay * (2 ^ attempt)`
- Rate limit: Use `Retry-After` header value

**Retryable Errors** (automatic retry):
- `rate_limited`
- `service_unavailable`
- `request_timeout`
- `internal_error`

**Non-Retryable Errors** (immediate failure):
- `channel_not_found`
- `not_in_channel`
- `invalid_auth`
- `token_revoked`
- `missing_scope`
- `account_inactive`
- `no_permission`

**Configuration**:
| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_RETRIES` | 3 | Maximum retry attempts |
| `RETRY_BASE_DELAY` | 1.0 | Base delay in seconds |

**Files**:
- `src/labslack/relay/__init__.py`
- `src/labslack/relay/message_relay.py`
- `tests/unit/test_message_relay.py`
- `tests/integration/test_message_relay.py`

---

## Story: LABSLACK-6 - Application Integration & Observability

**Type**: Story
**Status**: Done
**Priority**: High
**Sprint**: Phase 6

**Summary**: Integrate all components and add structured logging and metrics

**Description**:
Wire up all components in the main application, add structured JSON logging with contextual fields, and implement a metrics system for observability.

**Acceptance Criteria**:
- [x] Main `AsyncApp` application in `app.py`
- [x] All handlers and services wired together
- [x] aiohttp server with all endpoints
- [x] Structured logging with JSON format
- [x] Contextual log fields (user_id, source, error_code, etc.)
- [x] Configurable log format (`LOG_JSON` env var)
- [x] Metrics module (Counter, Gauge, Histogram)
- [x] GET `/metrics` endpoint returning JSON
- [x] Track: messages relayed, retries, errors by source
- [x] Integration tests for end-to-end flow
- [x] Manual test script

**Technical Details**:

**Structured Logging**:
- Location: `src/labslack/logging.py`
- Format: JSON with `timestamp`, `level`, `message`, and context fields
- Toggle: `LOG_JSON=true|false`

**Metrics System**:
- Location: `src/labslack/metrics.py`
- Types: Counter, Gauge, Histogram
- Labels: Support for dimensional metrics
- Endpoint: GET `/metrics` returns all metrics as JSON

**Metrics Tracked**:
| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `messages_relayed_total` | Counter | source | Total messages relayed |
| `relay_retries_total` | Counter | source, error | Total retry attempts |
| `relay_errors_total` | Counter | source, error | Total relay failures |

**API Endpoints** (complete):
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/slack/events` | Slack Signature | Slack events |
| POST | `/webhook` | X-API-Key | Webhook messages |
| GET | `/health` | None | Health check |
| GET | `/metrics` | None | Observability metrics |

**Files**:
- `src/labslack/app.py`
- `src/labslack/logging.py`
- `src/labslack/metrics.py`
- `tests/integration/test_app.py`
- `scripts/test_relay.py`

---

## Story: LABSLACK-7 - Documentation

**Type**: Story
**Status**: Done
**Priority**: Medium
**Sprint**: Phase 7

**Summary**: Create comprehensive project documentation

**Description**:
Write all user-facing and developer documentation including setup guides, architecture diagrams, and contribution guidelines.

**Acceptance Criteria**:
- [x] README.md with quick start guide
- [x] PROJECT_INSTRUCTIONS.md with detailed setup
- [x] DEVELOPMENT_PLAN.md with phased roadmap
- [x] FEATURE_REQUEST_TEMPLATE.md for proposals
- [x] CONTRIBUTING.md with development workflow
- [x] ARCHITECTURE.md with Mermaid diagrams
- [x] BDD feature files for all components
- [x] GitHub issue templates (bug, feature)
- [x] .env.example with all variables documented

**Documentation Created**:
| File | Purpose |
|------|---------|
| `README.md` | User-facing quick start |
| `docs/PROJECT_INSTRUCTIONS.md` | Detailed setup and development |
| `docs/DEVELOPMENT_PLAN.md` | Phased roadmap with status |
| `docs/ARCHITECTURE.md` | System diagrams (Mermaid) |
| `docs/FEATURE_REQUEST_TEMPLATE.md` | Feature proposal template |
| `CONTRIBUTING.md` | Contribution guidelines |
| `.github/ISSUE_TEMPLATE/` | Bug and feature issue forms |

**Architecture Diagrams**:
- System overview flowchart
- Component class diagram
- DM relay sequence diagram
- Webhook relay sequence diagram
- Error handling flowchart
- Configuration diagram
- Deployment architecture

---

## Task: LABSLACK-8 - Security Hardening

**Type**: Task
**Status**: Done
**Priority**: Medium
**Sprint**: Phase 7

**Summary**: Add security patterns to version control ignore files

**Description**:
Enhance `.gitignore` with comprehensive security patterns and create `.aiignore` to prevent AI assistants from indexing sensitive files.

**Acceptance Criteria**:
- [x] Add private key patterns (*.pem, *.key, id_rsa, etc.)
- [x] Add API key and token patterns
- [x] Add credentials file patterns
- [x] Add cloud provider credential directories
- [x] Add Slack-specific secret patterns
- [x] Add database and backup file patterns
- [x] Create `.aiignore` with same patterns
- [x] Commit with descriptive message

**Patterns Added**:
- Private keys: `*.pem`, `*.key`, `id_rsa`, `id_ed25519`, `*.ppk`
- Tokens: `*_token`, `api_key*`, `auth_token*`, `bearer_token*`
- Credentials: `credentials.*`, `secrets.*`, `.htpasswd`, `.netrc`
- Cloud: `.aws/`, `.azure/`, `.gcloud/`, `service-account*.json`
- Slack: `slack_token*`, `bot_token*`, `signing_secret*`
- Database: `*.sqlite`, `*.db`, `*.sql`, `dump.rdb`
- Infrastructure: `*.tfstate`, `.terraform/`, `*.vault`

---

# Upcoming Work

## Story: LABSLACK-9 - Production Hardening

**Type**: Story
**Status**: To Do
**Priority**: High
**Sprint**: Phase 8

**Summary**: Harden the application for production deployment

**Description**:
Add comprehensive error handling, rate limiting for the webhook endpoint, request ID tracking, and conduct a security audit.

**User Story**:
```
As an operations engineer
I want the bot to be production-hardened
So that it runs reliably under load and recovers from errors
```

**Acceptance Criteria**:
- [ ] Comprehensive error handling for all edge cases
- [ ] Rate limiting for webhook endpoint (prevent abuse)
- [ ] Request ID tracking (correlation across logs)
- [ ] Input sanitization audit
- [ ] Graceful degradation under high load
- [ ] All errors logged with full context
- [ ] Unit tests for error scenarios
- [ ] Load testing documentation

**Sub-Tasks**:

### LABSLACK-9.1 - Webhook Rate Limiting
**Type**: Sub-task
**Priority**: High

**Description**:
Implement rate limiting for the `/webhook` endpoint to prevent abuse and ensure stability under load.

**Technical Approach**:
- Token bucket or sliding window algorithm
- Configurable limits via environment variables
- Return 429 Too Many Requests when exceeded
- Include `Retry-After` header in response

**Configuration**:
| Variable | Default | Description |
|----------|---------|-------------|
| `WEBHOOK_RATE_LIMIT` | 100 | Requests per window |
| `WEBHOOK_RATE_WINDOW` | 60 | Window size in seconds |

**Acceptance Criteria**:
- [ ] Rate limiter middleware implemented
- [ ] Configurable via environment
- [ ] Returns 429 with Retry-After header
- [ ] Logs rate limit events
- [ ] Unit tests for rate limiting behavior

---

### LABSLACK-9.2 - Request ID Tracking
**Type**: Sub-task
**Priority**: Medium

**Description**:
Add unique request IDs to all incoming requests for end-to-end tracing and debugging.

**Technical Approach**:
- Generate UUID for each request
- Accept `X-Request-ID` header if provided (passthrough)
- Include in all log entries
- Return in response headers
- Propagate to Slack API calls

**Acceptance Criteria**:
- [ ] Request ID middleware implemented
- [ ] Accept external X-Request-ID header
- [ ] Generate UUID if not provided
- [ ] Include in all log entries
- [ ] Return in response X-Request-ID header
- [ ] Unit tests

---

### LABSLACK-9.3 - Security Audit
**Type**: Sub-task
**Priority**: High

**Description**:
Conduct security audit focusing on input validation, injection prevention, and secure defaults.

**Audit Areas**:
1. Input sanitization (webhook payload)
2. Header injection prevention
3. Log injection prevention
4. Secure default configurations
5. Dependency vulnerability scan
6. Secret handling review

**Acceptance Criteria**:
- [ ] All user input validated and sanitized
- [ ] No injection vulnerabilities
- [ ] Dependencies scanned for CVEs
- [ ] Security documentation updated
- [ ] Remediation of any findings

---

## Story: LABSLACK-10 - Containerization & Deployment

**Type**: Story
**Status**: To Do
**Priority**: High
**Sprint**: Phase 9

**Summary**: Containerize the application and create deployment artifacts

**Description**:
Create Docker image, compose files for local development, and optional Kubernetes manifests for production deployment.

**User Story**:
```
As a DevOps engineer
I want containerized deployment artifacts
So that I can deploy the bot consistently across environments
```

**Acceptance Criteria**:
- [ ] Multi-stage Dockerfile (minimal production image)
- [ ] docker-compose.yml for local development
- [ ] docker-compose.override.yml template for secrets
- [ ] Kubernetes manifests (Deployment, Service, ConfigMap, Secret)
- [ ] Health check integration with orchestrators
- [ ] Graceful shutdown handling (SIGTERM)
- [ ] Deployment documentation
- [ ] CI/CD pipeline configuration

**Sub-Tasks**:

### LABSLACK-10.1 - Dockerfile
**Type**: Sub-task
**Priority**: High

**Description**:
Create production-ready Dockerfile with multi-stage build.

**Technical Approach**:
```dockerfile
# Build stage
FROM python:3.12-slim AS builder
# Install uv, copy deps, build

# Production stage
FROM python:3.12-slim AS production
# Copy only runtime deps, non-root user
```

**Requirements**:
- Multi-stage build (small image size)
- Non-root user for security
- Health check instruction
- Proper signal handling

**Acceptance Criteria**:
- [ ] Multi-stage Dockerfile created
- [ ] Image size < 200MB
- [ ] Runs as non-root user
- [ ] HEALTHCHECK instruction included
- [ ] Documented build instructions

---

### LABSLACK-10.2 - Docker Compose
**Type**: Sub-task
**Priority**: Medium

**Description**:
Create docker-compose files for local development and testing.

**Files**:
- `docker-compose.yml` - Base configuration
- `docker-compose.override.yml.example` - Secret template

**Features**:
- Environment variable passthrough
- Volume mounts for development
- Health check integration
- Network configuration

**Acceptance Criteria**:
- [ ] docker-compose.yml created
- [ ] Override template for secrets
- [ ] Works with `docker-compose up`
- [ ] Documentation updated

---

### LABSLACK-10.3 - Kubernetes Manifests
**Type**: Sub-task
**Priority**: Low

**Description**:
Create Kubernetes manifests for production deployment.

**Manifests**:
- `deployment.yaml` - Pod specification
- `service.yaml` - Service exposure
- `configmap.yaml` - Non-sensitive configuration
- `secret.yaml` - Secret template
- `ingress.yaml` - Optional ingress

**Features**:
- Readiness and liveness probes
- Resource limits and requests
- Rolling update strategy
- Horizontal Pod Autoscaler (optional)

**Acceptance Criteria**:
- [ ] All manifests created
- [ ] Probes configured correctly
- [ ] Resource limits defined
- [ ] Works with `kubectl apply -k`
- [ ] Documentation updated

---

### LABSLACK-10.4 - Graceful Shutdown
**Type**: Sub-task
**Priority**: High

**Description**:
Implement graceful shutdown handling for container orchestrators.

**Technical Approach**:
- Handle SIGTERM signal
- Stop accepting new requests
- Complete in-flight requests
- Close Slack connections cleanly
- Exit with code 0

**Acceptance Criteria**:
- [ ] SIGTERM handler implemented
- [ ] In-flight requests completed
- [ ] Connections closed cleanly
- [ ] Exit code 0 on graceful shutdown
- [ ] Unit tests for shutdown behavior

---

### LABSLACK-10.5 - CI/CD Pipeline
**Type**: Sub-task
**Priority**: Medium

**Description**:
Create CI/CD pipeline configuration for automated testing and deployment.

**Pipeline Stages**:
1. Lint (ruff check)
2. Type check (mypy)
3. Unit tests
4. Integration tests
5. Build Docker image
6. Push to registry (on main)
7. Deploy (optional, manual trigger)

**Platforms** (choose one or more):
- GitHub Actions
- GitLab CI
- Jenkins

**Acceptance Criteria**:
- [ ] Pipeline configuration created
- [ ] All stages defined
- [ ] Runs on PR and push to main
- [ ] Docker image pushed on main
- [ ] Documentation updated

---

## Story: LABSLACK-11 - Message Filtering

**Type**: Story
**Status**: To Do
**Priority**: Medium
**Sprint**: Phase 10

**Summary**: Add keyword-based message filtering for relayed messages

**Description**:
Allow filtering of relayed messages based on configurable include/exclude keyword lists. Only messages matching criteria are forwarded.

**User Story**:
```
As a channel administrator
I want to filter relayed messages by keywords
So that only relevant messages appear in the relay channel
```

**Acceptance Criteria**:
- [ ] Filter supports include keywords (whitelist)
- [ ] Filter supports exclude keywords (blacklist)
- [ ] Keywords are case-insensitive
- [ ] Configurable via environment variables
- [ ] Filter can be disabled (default: no filtering)
- [ ] Applies to both DM and webhook messages
- [ ] BDD feature file created
- [ ] Unit tests for all filter scenarios
- [ ] Documentation updated

**Configuration**:
| Variable | Default | Description |
|----------|---------|-------------|
| `FILTER_INCLUDE_KEYWORDS` | (empty) | Comma-separated include list |
| `FILTER_EXCLUDE_KEYWORDS` | (empty) | Comma-separated exclude list |
| `FILTER_MODE` | `none` | Filter mode: none, include, exclude, both |

**BDD Scenarios**:
```gherkin
Feature: Message Filtering

  Scenario: Include messages with keyword
    Given the filter includes keyword "urgent"
    When a DM contains "This is urgent"
    Then the message should be relayed

  Scenario: Exclude messages with keyword
    Given the filter excludes keyword "test"
    When a DM contains "This is a test"
    Then the message should not be relayed

  Scenario: No filtering when disabled
    Given filtering is disabled
    When any message is received
    Then the message should be relayed
```

**Files**:
- `src/labslack/filters/__init__.py`
- `src/labslack/filters/keyword_filter.py`
- `tests/unit/test_keyword_filter.py`
- `docs/features/message_filtering.feature`

---

## Story: LABSLACK-12 - User Allowlist/Blocklist

**Type**: Story
**Status**: To Do
**Priority**: Medium
**Sprint**: Phase 10

**Summary**: Control which users can relay messages via DM

**Description**:
Implement user-based access control for DM relay, allowing administrators to define which users are allowed or blocked from relaying messages.

**User Story**:
```
As an administrator
I want to control which users can relay messages
So that I can prevent abuse and limit access
```

**Acceptance Criteria**:
- [ ] Support user allowlist (only these users can relay)
- [ ] Support user blocklist (these users are blocked)
- [ ] List mode: allowlist OR blocklist (not both)
- [ ] Configurable via environment variables
- [ ] Log blocked attempts at WARNING level
- [ ] BDD feature file created
- [ ] Unit tests
- [ ] Documentation updated

**Configuration**:
| Variable | Default | Description |
|----------|---------|-------------|
| `USER_LIST_MODE` | `none` | Mode: none, allow, block |
| `USER_ALLOWLIST` | (empty) | Comma-separated user IDs |
| `USER_BLOCKLIST` | (empty) | Comma-separated user IDs |

---

## Story: LABSLACK-13 - Multiple Relay Channels

**Type**: Story
**Status**: To Do
**Priority**: Low
**Sprint**: Phase 10

**Summary**: Route messages to different channels based on rules

**Description**:
Enable routing messages to different Slack channels based on configurable rules (source, keywords, user, etc.).

**User Story**:
```
As an administrator
I want to route messages to different channels
So that messages are organized by topic or source
```

**Acceptance Criteria**:
- [ ] Define routing rules via configuration
- [ ] Support routing by source (webhook)
- [ ] Support routing by keyword match
- [ ] Support routing by user ID
- [ ] Default channel for unmatched messages
- [ ] BDD feature file created
- [ ] Unit tests
- [ ] Documentation updated

**Example Configuration**:
```yaml
routes:
  - match:
      source: "jenkins"
    channel: "C_CICD_ALERTS"
  - match:
      keywords: ["urgent", "critical"]
    channel: "C_URGENT"
  - default:
    channel: "C_GENERAL_RELAY"
```

---

## Story: LABSLACK-14 - Slack Command Support

**Type**: Story
**Status**: To Do
**Priority**: Low
**Sprint**: Phase 10

**Summary**: Add slash command for relay configuration

**Description**:
Implement a `/relay` slash command for administrators to check status and manage configuration.

**User Story**:
```
As an administrator
I want to use slash commands to manage the bot
So that I can check status and configure without accessing the server
```

**Commands**:
| Command | Description |
|---------|-------------|
| `/relay status` | Show current configuration |
| `/relay stats` | Show relay statistics |
| `/relay help` | Show available commands |

**Acceptance Criteria**:
- [ ] Slash command handler implemented
- [ ] Status command shows configuration
- [ ] Stats command shows metrics
- [ ] Help command lists options
- [ ] Admin-only access control
- [ ] Unit tests
- [ ] Documentation updated

---

# Backlog Items

## Story: LABSLACK-B1 - Socket Mode Support

**Type**: Story
**Status**: Backlog
**Priority**: Medium
**Effort**: Medium

**Summary**: Add Socket Mode for firewalled environments

**Description**:
Enable Socket Mode as an alternative to HTTP mode for deployments behind firewalls that cannot expose public endpoints.

**User Story**:
```
As a DevOps engineer in a restricted network
I want to use Socket Mode
So that the bot works without public endpoints
```

**Technical Notes**:
- Use `slack-bolt` Socket Mode handler
- Configuration toggle: `CONNECTION_MODE=socket|http`
- Requires App-Level Token (`xapp-`)

---

## Story: LABSLACK-B2 - Multi-Workspace Support (OAuth)

**Type**: Story
**Status**: Backlog
**Priority**: Low
**Effort**: High

**Summary**: Support installation across multiple Slack workspaces

**Description**:
Implement OAuth 2.0 flow to allow the bot to be installed in multiple workspaces with per-workspace configuration.

**Technical Notes**:
- OAuth 2.0 installation flow
- Token storage (database required)
- Per-workspace configuration
- Significant architecture changes

---

## Story: LABSLACK-B3 - Web Dashboard

**Type**: Story
**Status**: Backlog
**Priority**: Low
**Effort**: High

**Summary**: Web-based configuration dashboard

**Description**:
Create a web dashboard for administrators to configure the bot without environment variables.

**Features**:
- View current configuration
- Update settings
- View metrics and logs
- User management (for multi-workspace)

---

## Story: LABSLACK-B4 - Block Kit Message Formatting

**Type**: Story
**Status**: Backlog
**Priority**: Medium
**Effort**: Medium

**Summary**: Use Slack Block Kit for rich message formatting

**Description**:
Enhance message formatting using Slack Block Kit for richer, more interactive messages.

**Features**:
- Structured sections
- Buttons and actions
- Collapsible content
- Rich metadata display

---

## Story: LABSLACK-B5 - Message History Database

**Type**: Story
**Status**: Backlog
**Priority**: Low
**Effort**: Medium

**Summary**: Store message history for auditing

**Description**:
Add database storage for relayed messages to enable auditing, analytics, and replay.

**Features**:
- Message persistence (SQLite/PostgreSQL)
- Query API for history
- Retention policy
- Analytics endpoint

---

# Labels Reference

| Label | Description |
|-------|-------------|
| `phase-1` through `phase-10` | Development phase |
| `priority-high` | High priority |
| `priority-medium` | Medium priority |
| `priority-low` | Low priority |
| `type-story` | User story |
| `type-task` | Technical task |
| `type-bug` | Bug fix |
| `component-formatter` | Message formatter |
| `component-dm-handler` | DM handler |
| `component-webhook` | Webhook handler |
| `component-relay` | Message relay |
| `component-observability` | Logging/metrics |
| `security` | Security-related |
| `documentation` | Documentation |
| `infrastructure` | CI/CD, deployment |

---

# Sprint Planning Notes

## Suggested Sprint Structure

**Sprint 1 (Phase 8)**: Production Hardening
- LABSLACK-9.1: Webhook Rate Limiting
- LABSLACK-9.2: Request ID Tracking
- LABSLACK-9.3: Security Audit

**Sprint 2 (Phase 9)**: Containerization
- LABSLACK-10.1: Dockerfile
- LABSLACK-10.2: Docker Compose
- LABSLACK-10.4: Graceful Shutdown

**Sprint 3 (Phase 9 continued)**: Deployment
- LABSLACK-10.3: Kubernetes Manifests
- LABSLACK-10.5: CI/CD Pipeline

**Sprint 4+ (Phase 10)**: Enhanced Features
- LABSLACK-11: Message Filtering
- LABSLACK-12: User Allowlist/Blocklist
- Additional features as prioritized

---

*Generated: 2026-01-27*
*Project: LabSlack Bot*
*Repository: https://github.com/redhat-openshift-partner-labs/labslack*
