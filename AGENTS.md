# Agent Guidelines: Logfire Content

This document provides guidelines for AI agents working on this repository.

## Project Overview

**logfire-content** is a repository containing:

1. **logfire-cli**: A Python CLI for managing Pydantic Logfire dashboards
2. **Perses Dashboard Content**: Pre-built dashboards for common infrastructure monitoring
3. **Documentation**: Query references and LLM generation guides for Logfire dashboards

## Commands

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

## Architecture

### CLI Structure

```
src/logfire_cli/
├── __init__.py      # Package exports
├── cli.py           # Click-based CLI commands
├── client.py        # Logfire API client (httpx)
├── models.py        # Pydantic models for API
└── py.typed         # Type hints marker
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

### Dashboard Format

Dashboards use native **Perses YAML** format with Logfire-specific query plugins:

```yaml
kind: Dashboard
metadata:
  name: my-dashboard
spec:
  display:
    name: "My Dashboard"
  panels:
    MyPanel:
      kind: Panel
      spec:
        queries:
          - kind: TimeSeriesQuery
            spec:
              plugin:
                kind: LogfireTimeSeriesQuery  # Logfire-specific
                spec:
                  query: "SELECT time_bucket($resolution, start_timestamp) AS x, ..."
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
- Prefer `httpx` for HTTP clients (async-ready)
- Use `pydantic` for data validation
- Use `rich-click` for CLI output

### Error Handling

- Define specific exception classes (e.g., `LogfireAuthenticationError`)
- Use context managers for resource cleanup
- Provide helpful error messages for CLI users

## Logfire Query Reference

### Tables

| Table | Use Case |
|-------|----------|
| `records` | Spans, logs, traces |
| `metrics` | OTel metrics (counters, gauges, histograms) |

### Key Fields - `records`

| Field | Type | Description |
|-------|------|-------------|
| `start_timestamp` | timestamp | When span started |
| `duration` | interval | Span duration |
| `span_name` | string | Operation name |
| `level` | string | Log level |
| `message` | string | Log message |
| `attributes` | jsonb | All OTel attributes |
| `trace_id` | string | Trace identifier |
| `span_id` | string | Span identifier |

### Key Fields - `metrics`

| Field | Type | Description |
|-------|------|-------------|
| `recorded_timestamp` | timestamp | When metric was recorded |
| `metric_name` | string | e.g., `system.cpu.utilization` |
| `scalar_value` | double | For counters/gauges |
| `histogram_count` | int | For histograms |
| `histogram_sum` | double | For histograms |
| `attributes` | jsonb | All OTel attributes |

### Special Variables

| Variable | Description |
|----------|-------------|
| `$resolution` | Auto-calculated time bucket (required for time series) |

### Query Patterns

```sql
-- Time series (for TimeSeriesChart)
SELECT
  time_bucket($resolution, start_timestamp) AS x,
  count(1) as y
FROM records
WHERE span_name = 'HTTP GET'
GROUP BY x
ORDER BY x;

-- Time series with series breakdown
SELECT
  time_bucket($resolution, recorded_timestamp) AS x,
  attributes->>'service.name' AS series,
  avg(scalar_value) AS y
FROM metrics
WHERE metric_name = 'system.cpu.utilization'
GROUP BY x, series
ORDER BY x;

-- Stat/Gauge (single value)
SELECT avg(scalar_value) * 100 AS value
FROM metrics
WHERE metric_name = 'system.memory.utilization'
  AND recorded_timestamp > now() - interval '5 minutes';
```

## Panel Types

| Kind | Use Case | Key Options |
|------|----------|-------------|
| `TimeSeriesChart` | Line/area over time | `legend.position`, `visual.connectNulls`, `yAxis.format` |
| `StatChart` | Single big number | `calculation`, `format`, `thresholds`, `sparkline` |
| `GaugeChart` | Gauge/meter | `calculation`, `format`, `thresholds`, `max` |
| `BarChart` | Bar charts | `calculation`, `format`, `orientation` |
| `Table` | Tabular data | `columnSettings` |
| `Markdown` | Static text | `text` |

## Testing

### Running Tests

```bash
make test              # Quick test run
make test-coverage     # With coverage report
```

### Test Structure

- Use `pytest` with `pytest-asyncio` for async tests
- Use `respx` for mocking HTTP requests
- Use `inline-snapshot` for snapshot testing
- Fixtures defined in `tests/conftest.py`

## Verification Checklist

Before committing changes:

1. Run `make ci` - all checks must pass
2. For CLI changes: test with actual Logfire instance if possible
3. For dashboard content: validate with `logfire-cli lint`
4. Update documentation if adding new features

## CI Failures

The CI pipeline fails on:

- Ruff lint errors
- Type check errors (basedpyright)
- Test failures
- Coverage below 80%

## Adding New Integrations

1. Create directory: `integrations/<technology>/`
2. Add `README.md` with setup instructions
3. Add `overview.yaml` with Perses dashboard
4. Add `collector.yaml` with OTel Collector config (if applicable)
5. Run `logfire-cli lint integrations/<technology>/overview.yaml`

## References

- [Perses Documentation](https://perses.dev/)
- [Perses Dashboard Schema](https://perses.dev/perses/docs/api/dashboard/)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [Logfire Documentation](https://logfire.pydantic.dev/docs/)
