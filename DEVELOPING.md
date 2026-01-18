# Development Guide

This guide is for developers contributing to the logfire-content project.

## Setup

```bash
# Clone repository
git clone https://github.com/strawgate/logfire-content.git
cd logfire-content

# Install dependencies
make sync
```

## Development Commands

| Command | Purpose |
|---------|---------|
| `make ci` | Run all CI checks (lint, typecheck, test) |
| `make check` | Alias for `make ci` |
| `make lint-check` | Check code with ruff |
| `make lint-fix` | Auto-fix linting issues |
| `make format` | Format code with ruff |
| `make typecheck` | Run basedpyright type checking |
| `make test` | Run tests with pytest |
| `make test-coverage` | Run tests with coverage report |
| `make docs` | Build documentation |
| `make docs-serve` | Serve documentation locally |
| `make sync` | Sync all dependencies |

## Project Structure

```
logfire-content/
├── src/logfire_cli/        # CLI source code
│   ├── cli.py              # Click commands
│   ├── clients/
│   │   └── logfire_api.py  # aiohttp API client
│   ├── models/
│   │   └── logfire_api.py  # Pydantic models
│   └── utilities/
│       ├── console.py      # Rich console utilities
│       └── file.py         # File I/O utilities
├── integrations/           # Dashboard content
│   └── host-metrics/       # Host metrics integration
├── docs/                   # Documentation
├── tests/                  # Test suite
│   └── clients/            # Client tests
├── pyproject.toml          # Project configuration
├── Makefile                # Development commands
└── AGENTS.md               # AI agent guidelines
```

## Architecture

### CLI Structure

```
src/logfire_cli/
├── __init__.py           # Package exports
├── cli.py                # Click-based CLI commands
├── clients/
│   └── logfire_api.py    # Logfire API client (aiohttp)
├── models/
│   └── logfire_api.py    # Pydantic models for API
├── utilities/
│   ├── console.py        # Rich console utilities
│   └── file.py           # File I/O utilities
└── py.typed              # Type hints marker
```

### Content Structure

```
integrations/
├── host-metrics/
│   ├── README.md           # Integration documentation
│   ├── overview.yaml       # Perses dashboard YAML
│   └── collector.yaml      # OTel Collector config
├── kubernetes/
├── postgresql/
└── ...
```

## Code Conventions

### Python Style

- **Line length**: 140 characters
- **Quotes**: Single quotes (`'`) for strings
- **Type hints**: Required for all public functions
- **Docstrings**: Google style, required for public APIs
- **Imports**: Sorted by isort (standard → third-party → first-party)

### Explicit Patterns

- Use explicit boolean comparisons: `if value is True:` not `if value:`
- Use `pathlib.Path` instead of string paths
- Prefer `aiohttp` for HTTP clients (async-ready)
- Use `pydantic` for data validation and type safety
- Use `rich-click` for CLI output
- Use typed Pydantic models instead of raw dictionaries for API responses

### Error Handling

- Define specific exception classes (e.g., `LogfireAuthenticationError`)
- Use context managers for resource cleanup
- Provide helpful error messages for CLI users

## Client API

The `LogfireClient` provides the following methods:

- `list_dashboards() -> ListDashboards` - List all dashboards
- `get_dashboard(slug: str) -> Dashboard` - Get a dashboard by slug
- `create_dashboard(slug: str, dashboard: Dashboard) -> Dashboard` - Create a new dashboard (POST)
- `update_dashboard(slug: str, dashboard: Dashboard) -> Dashboard` - Update an existing dashboard (PUT)
- `delete_dashboard(slug: str) -> None` - Delete a dashboard

All methods use strongly-typed Pydantic models (`Dashboard`, `ListDashboards`, etc.) instead of raw dictionaries.

### API URL Format

**Important**: All API endpoints require trailing slashes. URLs should be formatted as:
- `/ui-api/organizations/{org}/projects/{project}/dashboards/` (list)
- `/ui-api/organizations/{org}/projects/{project}/dashboards/{slug}/` (get/update/delete)

The client automatically appends trailing slashes to all endpoint URLs.

## Testing

### Running Tests

```bash
make test              # Quick test run
make test-coverage     # With coverage report
```

### Test Structure

- Use `pytest` with `pytest-asyncio` for async tests
- Use `aioresponses` for mocking HTTP requests (aiohttp)
- Use `inline-snapshot` for snapshot testing
- Fixtures defined in `tests/conftest.py`
- Client tests in `tests/clients/test_logfire_api.py`
- Integration tests in `tests/clients/test_logfire_api_integration.py`

## Adding New Integrations

1. Create directory: `integrations/<technology>/`
2. Add `README.md` with setup instructions
3. Add `overview.yaml` with Perses dashboard
4. Add `collector.yaml` with OTel Collector config (if applicable)
5. Run `logfire-cli lint integrations/<technology>/overview.yaml`

## Verification Checklist

Before committing changes:

1. Run `make ci` - all checks must pass
2. For CLI changes: test with actual Logfire instance if possible
3. For dashboard content: validate with `logfire-cli dashboards lint` (or `logfire-cli lint`)
4. Update documentation if adding new features
5. Ensure all API endpoints use trailing slashes (`/dashboards/`, not `/dashboards`)

## CI Failures

The CI pipeline fails on:

- Ruff lint errors
- Type check errors (basedpyright)
- Test failures
- Coverage below 80%

## References

- [Perses Documentation](https://perses.dev/)
- [Perses Dashboard Schema](https://perses.dev/perses/docs/api/dashboard/)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [Logfire Documentation](https://logfire.pydantic.dev/docs/)
