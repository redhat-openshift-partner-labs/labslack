# Contributing to LabSlack

Thank you for your interest in contributing to LabSlack! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Commit Messages](#commit-messages)
- [Proposing Features](#proposing-features)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the issue, not the person
- Help others learn and grow

## Getting Started

1. **Check existing issues** to see if your contribution idea is already being discussed
2. **Read the [Development Plan](docs/DEVELOPMENT_PLAN.md)** to understand current priorities
3. **Review [Project Instructions](docs/PROJECT_INSTRUCTIONS.md)** for detailed setup and architecture

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- A Slack workspace for testing (recommended: create a test workspace)

### Installation

```bash
# Clone the repository
git clone https://github.com/redhat-openshift-partner-labs/labslack.git
cd labslack

# Install dependencies
uv sync --all-extras

# Copy environment template
cp .env.example .env
# Edit .env with your Slack credentials
```

### Slack App Setup

See [Project Instructions - Slack App Configuration](docs/PROJECT_INSTRUCTIONS.md#slack-app-configuration) for detailed setup steps.

## Development Workflow

This project follows **Test-Driven Development (TDD)** and **Behavior-Driven Development (BDD)**.

### For Bug Fixes

1. Write a failing test that reproduces the bug
2. Fix the bug (make the test pass)
3. Verify no regressions with `uv run pytest`
4. Submit PR

### For New Features

1. Check if feature is in [Development Plan](docs/DEVELOPMENT_PLAN.md) or [Backlog](docs/DEVELOPMENT_PLAN.md#backlog)
2. If not, [propose the feature](#proposing-features) first
3. Write BDD feature file in `docs/features/`
4. Write unit tests (Red)
5. Implement minimum code to pass (Green)
6. Refactor while keeping tests passing (Refactor)
7. Update documentation if user-facing
8. Submit PR

### Development Commands

```bash
# Run the bot locally
uv run python -m labslack.app

# Expose via ngrok (for Slack event subscriptions)
ngrok http 3000
```

## Testing

All contributions must include appropriate tests.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/labslack --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_message_formatter.py -v

# Run tests matching a pattern
uv run pytest -k "test_dm" -v
```

### Test Organization

| Directory | Purpose |
|-----------|---------|
| `tests/unit/` | Unit tests for individual components |
| `tests/integration/` | Integration tests for component interactions |
| `tests/bdd/` | BDD step implementations |
| `docs/features/` | Gherkin feature specifications |

### Manual Testing

```bash
# Test health endpoint
uv run python scripts/test_relay.py health

# Test webhook
uv run python scripts/test_relay.py webhook "Test message"

# Test direct Slack message
uv run python scripts/test_relay.py dm "Test message"
```

## Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make your changes** following TDD workflow

3. **Ensure all tests pass**:
   ```bash
   uv run pytest
   ```

4. **Check code quality**:
   ```bash
   uv run ruff check src/
   uv run ruff format --check src/
   uv run mypy src/
   ```

5. **Commit with conventional message** (see [Commit Messages](#commit-messages))

6. **Push your branch** and create a Pull Request

7. **PR Requirements**:
   - All tests passing
   - Code follows project style
   - Documentation updated (if applicable)
   - Descriptive PR title and description

## Code Style

### Formatting and Linting

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

```bash
# Check for issues
uv run ruff check src/

# Auto-fix issues
uv run ruff check --fix src/

# Format code
uv run ruff format src/

# Type checking
uv run mypy src/
```

### Code Guidelines

- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Keep functions focused and small
- Use async/await consistently (this is an async-first project)
- Follow existing patterns in the codebase

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>: <description>

[optional body]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `test` | Adding or updating tests |
| `docs` | Documentation changes |
| `refactor` | Code refactoring (no behavior change) |
| `chore` | Maintenance tasks |
| `style` | Code style/formatting changes |

### Examples

```
feat: add message filtering by keywords

fix: handle empty webhook payload gracefully

test: add integration tests for rate limiting

docs: update README with new environment variables

refactor: extract message validation to separate function
```

## Proposing Features

For significant new features:

1. **Check the [Development Plan](docs/DEVELOPMENT_PLAN.md)** to see if it's already planned
2. **Open a GitHub Issue** using the Feature Request template
3. **Or use the [Feature Request Template](docs/FEATURE_REQUEST_TEMPLATE.md)** for detailed proposals
4. **Include a BDD user story** when possible:
   ```gherkin
   As a [type of user],
   I want [goal/desire],
   So that [benefit/value].

   Scenario: [Scenario Name]
     Given [precondition]
     When [action]
     Then [expected result]
   ```

## Questions?

- Check existing documentation in `docs/`
- Open a GitHub issue with your question
- Review the codebase for examples of similar implementations

---

Thank you for contributing to LabSlack!
