# Claude Code Instructions for LabSlack

## Git Policy
- **NEVER push to remote repository** - User handles all pushes manually
- **DO make frequent incremental commits** - Small, focused commits for easy rollback
- Use conventional commit messages (feat:, fix:, test:, docs:, refactor:, chore:)

## Role Context
- Expert Python developer
- Expert Slack administrator
- Expert Slack bot developer
- Expert with slack-bolt Python library

## Development Approach
- TDD: Write tests first
- BDD: Use Gherkin feature files
- Async-first: Use AsyncApp and async/await throughout
- Use mermaid for documentation diagrams

## Key Files
- `docs/PROJECT_INSTRUCTIONS.md` - Full project guide
- `docs/DEVELOPMENT_PLAN.md` - Development phases and status
- `docs/FEATURE_REQUEST_TEMPLATE.md` - Feature proposal template
- `.github/ISSUE_TEMPLATE/` - GitHub issue forms

## Testing
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Manual testing: `scripts/test_relay.py`
- Run all: `uv run pytest`

## Running the Bot
```bash
uv run python -m labslack.app
```
