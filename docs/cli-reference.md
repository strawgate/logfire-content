# CLI Reference

Complete command reference for `logfire-cli`.

## Installation

```bash
pip install logfire-cli
# or with uv
uv pip install logfire-cli
```

## Configuration

Configure via environment variables or command-line options:

| Environment Variable | CLI Option | Description |
|---------------------|------------|-------------|
| `LOGFIRE_TOKEN` | `--token` | API authentication token |
| `LOGFIRE_ORGANIZATION` | `-o, --organization` | Organization slug |
| `LOGFIRE_PROJECT` | `-p, --project` | Project slug |
| `LOGFIRE_BASE_URL` | `--base-url` | API base URL (default: US region) |

### Example Configuration

```bash
export LOGFIRE_TOKEN="your-api-token"
export LOGFIRE_ORGANIZATION="my-org"
export LOGFIRE_PROJECT="my-project"
```

## Commands

### `logfire-cli list`

List all dashboards in the project.

```bash
logfire-cli list
```

**Output:**

```
┌──────────────────┬─────────────────────┬─────────────────────┐
│ Slug             │ Name                │ Updated             │
├──────────────────┼─────────────────────┼─────────────────────┤
│ host-metrics     │ Host Metrics        │ 2024-01-15T10:30:00 │
│ api-performance  │ API Performance     │ 2024-01-14T15:45:00 │
└──────────────────┴─────────────────────┴─────────────────────┘
```

### `logfire-cli pull`

Export a dashboard to a YAML file.

```bash
logfire-cli pull <slug> [-o OUTPUT]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `slug` | Dashboard identifier |

**Options:**

| Option | Description |
|--------|-------------|
| `-o, --output` | Output file path (default: `<slug>.yaml`) |

**Examples:**

```bash
# Export to default filename
logfire-cli pull host-metrics

# Export to specific file
logfire-cli pull host-metrics -o dashboards/host.yaml
```

### `logfire-cli push`

Import a YAML dashboard to Logfire.

```bash
logfire-cli push <file> [-s SLUG]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `file` | Path to YAML dashboard file |

**Options:**

| Option | Description |
|--------|-------------|
| `-s, --slug` | Override dashboard slug (default: derived from metadata.name) |

**Examples:**

```bash
# Push using name from YAML
logfire-cli push my-dashboard.yaml

# Push with explicit slug
logfire-cli push my-dashboard.yaml -s custom-slug
```

### `logfire-cli get`

Print dashboard YAML to stdout.

```bash
logfire-cli get <slug>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `slug` | Dashboard identifier |

**Examples:**

```bash
# View dashboard
logfire-cli get host-metrics

# Pipe to file
logfire-cli get host-metrics > host-metrics.yaml

# Pipe to another tool
logfire-cli get host-metrics | yq '.spec.panels'
```

### `logfire-cli delete`

Delete a dashboard.

```bash
logfire-cli delete <slug> [-y]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `slug` | Dashboard identifier |

**Options:**

| Option | Description |
|--------|-------------|
| `-y, --yes` | Skip confirmation prompt |

**Examples:**

```bash
# Delete with confirmation
logfire-cli delete old-dashboard

# Delete without confirmation
logfire-cli delete old-dashboard -y
```

### `logfire-cli lint`

Validate dashboard YAML files.

```bash
logfire-cli lint <files...> [--strict]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `files` | One or more YAML files to validate |

**Options:**

| Option | Description |
|--------|-------------|
| `--strict` | Treat warnings as errors |

**Examples:**

```bash
# Validate single file
logfire-cli lint my-dashboard.yaml

# Validate multiple files
logfire-cli lint dashboards/*.yaml

# Strict mode
logfire-cli lint my-dashboard.yaml --strict
```

**Notes:**

- If `percli` is installed, uses full Perses schema validation
- Otherwise, performs basic structure validation

### `logfire-cli init`

Create a new dashboard template.

```bash
logfire-cli init <name> [-o OUTPUT]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Display name for the dashboard |

**Options:**

| Option | Description |
|--------|-------------|
| `-o, --output` | Output file path (default: slugified name) |

**Examples:**

```bash
# Create template
logfire-cli init "My New Dashboard"
# Creates: my-new-dashboard.yaml

# Specify output path
logfire-cli init "API Metrics" -o dashboards/api.yaml
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error (authentication, not found, validation failure) |

## Examples

### Complete Workflow

```bash
# Configure
export LOGFIRE_TOKEN="your-token"
export LOGFIRE_ORGANIZATION="my-org"
export LOGFIRE_PROJECT="my-project"

# Create new dashboard
logfire-cli init "API Performance"

# Edit the template
vim api-performance.yaml

# Validate
logfire-cli lint api-performance.yaml

# Push to Logfire
logfire-cli push api-performance.yaml

# Verify
logfire-cli list

# Make changes in Logfire UI, then pull
logfire-cli pull api-performance

# Delete when no longer needed
logfire-cli delete api-performance
```

### Bulk Operations

```bash
# Export all dashboards
for slug in $(logfire-cli list | tail -n +4 | awk '{print $2}'); do
  logfire-cli pull "$slug" -o "backup/$slug.yaml"
done

# Validate all YAML files
logfire-cli lint integrations/*/*.yaml

# Push all integrations
for f in integrations/*/overview.yaml; do
  logfire-cli push "$f"
done
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Validate Dashboards
  run: |
    pip install logfire-cli
    logfire-cli lint integrations/*/*.yaml

- name: Deploy Dashboards
  env:
    LOGFIRE_TOKEN: ${{ secrets.LOGFIRE_TOKEN }}
    LOGFIRE_ORGANIZATION: my-org
    LOGFIRE_PROJECT: production
  run: |
    for f in integrations/*/overview.yaml; do
      logfire-cli push "$f"
    done
```
