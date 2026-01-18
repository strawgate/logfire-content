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
logfire-cli dashboards list
```

Note: All commands are under the `dashboards` subcommand group.

### Create a Dashboard

```bash
# Create from template
logfire-cli dashboards init "My Dashboard"

# Edit my-dashboard.yaml, then push
logfire-cli dashboards push my-dashboard.yaml
```

### Pull and Modify

```bash
# Export existing dashboard
logfire-cli dashboards pull my-dashboard -o my-dashboard.yaml

# Edit and push back
logfire-cli dashboards push my-dashboard.yaml
```

### Validate Dashboards

```bash
logfire-cli lint my-dashboard.yaml
# or
logfire-cli dashboards lint my-dashboard.yaml
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `logfire-cli dashboards list` | List all dashboards |
| `logfire-cli dashboards pull <slug>` | Export dashboard to YAML |
| `logfire-cli dashboards push <file>` | Import YAML to Logfire (creates or updates) |
| `logfire-cli dashboards get <slug>` | Print dashboard YAML |
| `logfire-cli dashboards delete <slug>` | Delete a dashboard |
| `logfire-cli dashboards init <name>` | Create dashboard template |
| `logfire-cli lint <files>` | Validate YAML files |

All dashboard operations use strongly-typed Pydantic models for type safety and validation.

## Integrations

Pre-built dashboards for common technologies:

| Integration | Description |
|-------------|-------------|
| [host-metrics](integrations/host-metrics/) | System CPU, memory, disk, network |

### Deploy an Integration

```bash
logfire-cli dashboards push integrations/host-metrics/overview.yaml
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

## Contributing

For development setup and contribution guidelines, see [DEVELOPING.md](DEVELOPING.md).

## License

MIT
