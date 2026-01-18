# Logfire Content

Welcome to the Logfire Content documentation. This repository contains:

1. **logfire-cli**: A command-line tool for managing Pydantic Logfire dashboards
2. **Integrations**: Pre-built dashboards for common infrastructure monitoring
3. **Reference**: Documentation for building your own Logfire dashboards

## Quick Start

### Install the CLI

```bash
pip install logfire-cli
# or with uv
uv pip install logfire-cli
```

### Configure Authentication

```bash
export LOGFIRE_TOKEN="your-token"
export LOGFIRE_ORGANIZATION="your-org"
export LOGFIRE_PROJECT="your-project"
```

### List Dashboards

```bash
logfire-cli dashboards list
```

### Create a New Dashboard

```bash
logfire-cli dashboards init "My Dashboard"
# Edit my-dashboard.yaml
logfire-cli dashboards import my-dashboard.yaml
```

### Export an Existing Dashboard

```bash
logfire-cli dashboards export my-dashboard -o my-dashboard.yaml
```

## Documentation

- [CLI Reference](cli-reference.md) - Complete command documentation
- [Query Reference](query-reference.md) - Logfire SQL query patterns
- [Panel Types](panel-types.md) - Available Perses panel types
- [LLM Generation Guide](llm-generation-guide.md) - How to prompt for dashboards

## Integrations

Pre-built dashboards for common technologies:

- [Host Metrics](../integrations/host-metrics/README.md) - System CPU, memory,
  disk, network

## Contributing

See [AGENTS.md](../AGENTS.md) for development guidelines.
