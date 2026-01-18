# Logfire Content

CLI and content packs for managing [Pydantic Logfire](https://logfire.pydantic.dev/) dashboards.

## Overview

This repository provides:

1. **logfire-cli**: A command-line tool for managing Logfire dashboards
2. **Integrations**: Pre-built [Perses](https://perses.dev/) dashboards for common infrastructure
3. **Documentation**: Query references and guides for building dashboards

## Installation

```bash
pip install logfire-cli
# or with uv
uv pip install logfire-cli
```

## Quick Start

### Configure Authentication

```bash
export LOGFIRE_TOKEN="your-api-token"
export LOGFIRE_ORGANIZATION="your-org"
export LOGFIRE_PROJECT="your-project"
```

### List Dashboards

```bash
logfire-cli list
```

### Create a Dashboard

```bash
# Create from template
logfire-cli init "My Dashboard"

# Edit my-dashboard.yaml, then push
logfire-cli push my-dashboard.yaml
```

### Pull and Modify

```bash
# Export existing dashboard
logfire-cli pull my-dashboard -o my-dashboard.yaml

# Edit and push back
logfire-cli push my-dashboard.yaml
```

### Validate Dashboards

```bash
logfire-cli lint my-dashboard.yaml
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `logfire-cli list` | List all dashboards |
| `logfire-cli pull <slug>` | Export dashboard to YAML |
| `logfire-cli push <file>` | Import YAML to Logfire |
| `logfire-cli get <slug>` | Print dashboard YAML |
| `logfire-cli delete <slug>` | Delete a dashboard |
| `logfire-cli lint <files>` | Validate YAML files |
| `logfire-cli init <name>` | Create dashboard template |

## Integrations

Pre-built dashboards for common technologies:

| Integration | Description |
|-------------|-------------|
| [host-metrics](integrations/host-metrics/) | System CPU, memory, disk, network |

### Deploy an Integration

```bash
logfire-cli push integrations/host-metrics/overview.yaml
```

## Dashboard Format

Dashboards use the [Perses](https://perses.dev/) YAML format with Logfire-specific query plugins:

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
        plugin:
          kind: TimeSeriesChart
          spec:
            legend:
              position: bottom
        queries:
          - kind: TimeSeriesQuery
            spec:
              plugin:
                kind: LogfireTimeSeriesQuery
                spec:
                  query: |
                    SELECT
                      time_bucket($resolution, start_timestamp) AS x,
                      count(1) AS y
                    FROM records
                    GROUP BY x
                    ORDER BY x
  layouts:
    - kind: Grid
      spec:
        items:
          - x: 0
            y: 0
            width: 12
            height: 6
            content:
              $ref: "#/spec/panels/MyPanel"
```

## Documentation

- [CLI Reference](docs/cli-reference.md)
- [Query Reference](docs/query-reference.md)
- [Panel Types](docs/panel-types.md)
- [LLM Generation Guide](docs/llm-generation-guide.md)

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/strawgate/logfire-content.git
cd logfire-content

# Install dependencies
make sync
```

### Commands

```bash
make ci          # Run all checks
make lint-fix    # Fix linting issues
make typecheck   # Type checking
make test        # Run tests
make docs-serve  # Preview documentation
```

### Project Structure

```
logfire-content/
├── src/logfire_cli/        # CLI source code
│   ├── cli.py              # Click commands
│   ├── client.py           # API client
│   └── models.py           # Pydantic models
├── integrations/           # Dashboard content
│   └── host-metrics/       # Host metrics integration
├── docs/                   # Documentation
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
├── Makefile                # Development commands
└── AGENTS.md               # AI agent guidelines
```

## License

MIT
