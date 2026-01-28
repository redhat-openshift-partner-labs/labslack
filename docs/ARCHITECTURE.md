# LabSlack Architecture

This document describes the architecture of the LabSlack bot using Mermaid diagrams.

## System Overview

LabSlack is a Slack bot that relays messages from two sources to a designated Slack channel:
1. **Direct Messages (DMs)** sent to the bot
2. **External webhooks** from other systems

```mermaid
flowchart TB
    subgraph External Sources
        User[Slack User]
        ExtSys[External System<br/>CI/CD, Monitoring, etc.]
    end

    subgraph LabSlack Bot
        direction TB
        SlackEvents["/slack/events<br/>Event Handler"]
        Webhook["/webhook<br/>Webhook Handler"]
        Health["/health"]
        Metrics["/metrics"]

        subgraph Core Services
            Formatter[MessageFormatter]
            Relay[MessageRelay]
        end
    end

    subgraph Slack Platform
        SlackAPI[Slack Web API]
        Channel[Relay Channel]
    end

    User -->|Send DM| SlackEvents
    ExtSys -->|POST + API Key| Webhook
    SlackEvents --> Formatter
    Webhook --> Formatter
    Formatter --> Relay
    Relay -->|chat.postMessage| SlackAPI
    SlackAPI --> Channel
```

## Component Architecture

### Module Structure

```mermaid
classDiagram
    class App {
        +AsyncApp slack_app
        +WebClient client
        +Config config
        +MessageFormatter formatter
        +MessageRelay relay
        +start()
    }

    class Config {
        +str slack_bot_token
        +str slack_signing_secret
        +str relay_channel_id
        +str webhook_api_key
        +bool include_metadata
        +int max_retries
        +float retry_base_delay
        +from_env()
    }

    class MessageFormatter {
        +bool include_metadata
        +format_dm_message()
        +format_webhook_message()
    }

    class MessageRelay {
        +WebClient client
        +str channel_id
        +int max_retries
        +float base_delay
        +relay_message()
    }

    class WebhookHandler {
        +str api_key
        +handle_webhook()
        +health_check()
    }

    App --> Config
    App --> MessageFormatter
    App --> MessageRelay
    App --> WebhookHandler
    MessageRelay --> MessageFormatter
```

## Message Flow

### DM Relay Flow

```mermaid
sequenceDiagram
    participant User as Slack User
    participant Slack as Slack Platform
    participant Bot as LabSlack Bot
    participant Relay as MessageRelay
    participant Channel as Relay Channel

    User->>Slack: Send DM to bot
    Slack->>Bot: POST /slack/events<br/>(message.im event)

    Bot->>Bot: Validate signature
    Bot->>Bot: Filter (skip bots, subtypes)
    Bot->>Bot: Format message

    Bot->>Relay: relay_message()
    Relay->>Slack: chat.postMessage

    alt Success
        Slack->>Channel: Post message
        Slack-->>Relay: OK
        Relay-->>Bot: Success
    else Rate Limited
        Slack-->>Relay: rate_limited + Retry-After
        Relay->>Relay: Wait (exponential backoff)
        Relay->>Slack: Retry chat.postMessage
    else Non-Retryable Error
        Slack-->>Relay: Error (channel_not_found, etc.)
        Relay-->>Bot: Failure
        Bot->>Bot: Log error
    end
```

### Webhook Relay Flow

```mermaid
sequenceDiagram
    participant Ext as External System
    participant Bot as LabSlack Bot
    participant Relay as MessageRelay
    participant Slack as Slack API
    participant Channel as Relay Channel

    Ext->>Bot: POST /webhook<br/>X-API-Key: secret<br/>{"message": "..."}

    alt Invalid API Key
        Bot-->>Ext: 401 Unauthorized
    else Missing Message
        Bot-->>Ext: 400 Bad Request
    else Valid Request
        Bot->>Bot: Validate payload
        Bot->>Bot: Format message
        Bot->>Relay: relay_message()
        Relay->>Slack: chat.postMessage
        Slack->>Channel: Post message
        Slack-->>Relay: OK
        Relay-->>Bot: Success
        Bot-->>Ext: 200 OK
    end
```

## Error Handling & Retry Logic

```mermaid
flowchart TD
    A[Slack API Call] --> B{Response}

    B -->|Success| C[Return Success]

    B -->|Error| D{Retryable?}

    D -->|Yes| E{Attempts < Max?}
    E -->|Yes| F[Calculate Backoff]
    F --> G{Rate Limited?}
    G -->|Yes| H[Use Retry-After Header]
    G -->|No| I[Exponential Backoff<br/>base * 2^attempt]
    H --> J[Wait]
    I --> J
    J --> A

    E -->|No| K[Return Failure<br/>Max Retries Exceeded]
    D -->|No| L[Return Failure<br/>Non-Retryable Error]

    subgraph Retryable Errors
        R1[rate_limited]
        R2[service_unavailable]
        R3[request_timeout]
        R4[internal_error]
    end

    subgraph Non-Retryable Errors
        N1[channel_not_found]
        N2[not_in_channel]
        N3[invalid_auth]
        N4[token_revoked]
        N5[missing_scope]
    end
```

## API Endpoints

```mermaid
flowchart LR
    subgraph Endpoints
        E1[POST /slack/events]
        E2[POST /webhook]
        E3[GET /health]
        E4[GET /metrics]
    end

    subgraph Authentication
        A1[Slack Signature]
        A2[X-API-Key Header]
        A3[None]
    end

    subgraph Purpose
        P1[Slack Event Subscription]
        P2[External Message Ingestion]
        P3[Health Monitoring]
        P4[Observability Metrics]
    end

    E1 --- A1 --- P1
    E2 --- A2 --- P2
    E3 --- A3 --- P3
    E4 --- A3 --- P4
```

## Data Flow Overview

```mermaid
flowchart LR
    subgraph Input
        DM[DM Event]
        WH[Webhook POST]
    end

    subgraph Processing
        Filter[Filter<br/>Skip bots/subtypes]
        Auth[Authenticate<br/>API Key]
        Format[Format Message<br/>Add metadata]
    end

    subgraph Output
        Relay[Relay Service<br/>With retry logic]
        Channel[Slack Channel]
    end

    DM --> Filter --> Format --> Relay --> Channel
    WH --> Auth --> Format
```

## Configuration

```mermaid
flowchart TD
    subgraph Environment Variables
        direction LR
        REQ[Required]
        OPT[Optional]
    end

    subgraph Required
        R1[SLACK_BOT_TOKEN]
        R2[SLACK_SIGNING_SECRET]
        R3[RELAY_CHANNEL_ID]
    end

    subgraph Optional
        O1[WEBHOOK_API_KEY]
        O2[INCLUDE_METADATA]
        O3[HOST / PORT]
        O4[LOG_LEVEL / LOG_JSON]
        O5[MAX_RETRIES]
        O6[RETRY_BASE_DELAY]
    end

    subgraph Config Dataclass
        CFG[Config.from_env]
    end

    REQ --> CFG
    OPT --> CFG
    CFG --> App[Application]
```

## Deployment Architecture

```mermaid
flowchart TB
    subgraph Internet
        SlackCloud[Slack Cloud]
        ExtServices[External Services]
    end

    subgraph Your Infrastructure
        LB[Load Balancer / Reverse Proxy]

        subgraph Container/Process
            Bot[LabSlack Bot<br/>aiohttp server]
        end

        Monitor[Monitoring System]
    end

    SlackCloud -->|Events| LB
    ExtServices -->|Webhooks| LB
    LB --> Bot
    Bot -->|API Calls| SlackCloud
    Bot -->|/health, /metrics| Monitor
```

## Technology Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12+ |
| Async Framework | asyncio |
| Slack SDK | slack-bolt (AsyncApp) |
| HTTP Server | aiohttp |
| Testing | pytest, pytest-bdd, pytest-asyncio |
| Linting | Ruff |
| Type Checking | mypy |
| Package Manager | uv |

---

*Diagrams rendered with [Mermaid](https://mermaid.js.org/). View in GitHub or any Mermaid-compatible viewer.*
