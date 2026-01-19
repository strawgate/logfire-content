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

|Environment Variable|CLI Option|Description|
|---|---|---|
|`LOGFIRE_TOKEN`|`--token`|API authentication token|
|`LOGFIRE_ORGANIZATION`|`-o, --organization`|Organization slug|
|`LOGFIRE_PROJECT`|`-p, --project`|Project slug|
|`LOGFIRE_BASE_URL`|`--base-url`|API base URL (default: US region)|

### Example Configuration

```bash
export LOGFIRE_TOKEN="your-api-token"
export LOGFIRE_ORGANIZATION="my-org"
export LOGFIRE_PROJECT="my-project"
```

## Commands

### `logfire-cli dashboards list`

List all dashboards in the project.

```bash
logfire-cli dashboards list
```

**Output:**

```text
┌──────────────────┬─────────────────────┬─────────────────────┐
│ Slug             │ Name                │ Updated             │
├──────────────────┼─────────────────────┼─────────────────────┤
│ host-metrics     │ Host Metrics        │ 2024-01-15T10:30:00 │
│ api-performance  │ API Performance     │ 2024-01-14T15:45:00 │
└──────────────────┴─────────────────────┴─────────────────────┘
```

### `logfire-cli dashboards export`

Export a dashboard to a YAML file.

```bash
logfire-cli dashboards export <slug> [-o OUTPUT]
```

**Arguments:**

| Argument | Description           |
| -------- | --------------------- |
| `slug`   | Dashboard identifier  |

**Options:**

|Option|Description|
|---|---|
|`-o, --output`|Output file path (default: `<slug>.yaml`)|

**Examples:**

```bash
# Export to default filename
logfire-cli dashboards export host-metrics

# Export to specific file
logfire-cli dashboards export host-metrics -o dashboards/host.yaml
```

### `logfire-cli dashboards import`

Import a YAML dashboard to Logfire.

```bash
logfire-cli dashboards import <file> [-s SLUG]
```

**Arguments:**

| Argument | Description                  |
| -------- | ---------------------------- |
| `file`   | Path to YAML dashboard file  |

**Options:**

| Option        | Description                                    |
| ------------- | ---------------------------------------------- |
| `-s, --slug`  | Override dashboard slug (default: derived from |
|               | metadata.name)                                 |

**Examples:**

```bash
# Import using name from YAML
logfire-cli dashboards import my-dashboard.yaml

# Import with explicit slug
logfire-cli dashboards import my-dashboard.yaml -s custom-slug
```

### `logfire-cli dashboards get`

Print dashboard YAML to stdout.

```bash
logfire-cli dashboards get <slug>
```

**Arguments:**

| Argument | Description           |
| -------- | --------------------- |
| `slug`   | Dashboard identifier  |

**Examples:**

```bash
# View dashboard
logfire-cli dashboards get host-metrics

# Pipe to file
logfire-cli dashboards get host-metrics > host-metrics.yaml

# Pipe to another tool
logfire-cli dashboards get host-metrics | yq '.spec.panels'
```

### `logfire-cli dashboards delete`

Delete a dashboard.

```bash
logfire-cli dashboards delete <slug> [-y]
```

**Arguments:**

| Argument | Description           |
| -------- | --------------------- |
| `slug`   | Dashboard identifier  |

**Options:**

|Option|Description|
|---|---|
|`-y, --yes`|Skip confirmation prompt|

**Examples:**

```bash
# Delete with confirmation
logfire-cli dashboards delete old-dashboard

# Delete without confirmation
logfire-cli dashboards delete old-dashboard -y
```

### `logfire-cli dashboards init`

Create a new dashboard template.

```bash
logfire-cli dashboards init <name> [-o OUTPUT]
```

**Arguments:**

|Argument|Description|
|---|---|
|`name`|Display name for the dashboard|

**Options:**

|Option|Description|
|---|---|
|`-o, --output`|Output file path (default: slugified name)|

**Examples:**

```bash
# Create template
logfire-cli dashboards init "My New Dashboard"
# Creates: my-new-dashboard.yaml

# Specify output path
logfire-cli dashboards init "API Metrics" -o dashboards/api.yaml
```

## Exit Codes

|Code|Description|
|---|---|
|0|Success|
|1|Error (authentication, not found, validation failure)|

## Examples

### Complete Workflow

```bash
# Configure
export LOGFIRE_TOKEN="your-token"
export LOGFIRE_ORGANIZATION="my-org"
export LOGFIRE_PROJECT="my-project"

# Create new dashboard
logfire-cli dashboards init "API Performance"

# Edit the template
vim api-performance.yaml

# Import to Logfire
logfire-cli dashboards import api-performance.yaml

# Verify
logfire-cli dashboards list

# Make changes in Logfire UI, then export
logfire-cli dashboards export api-performance

# Delete when no longer needed
logfire-cli dashboards delete api-performance
```

### Bulk Operations

```bash
# Export all dashboards
for slug in $(logfire-cli dashboards list | tail -n +4 | awk '{print $2}'); do
  logfire-cli dashboards export "$slug" -o "backup/$slug.yaml"
done

# Import all integrations
for f in integrations/*/overview.yaml; do
  logfire-cli dashboards import "$f"
done
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Deploy Dashboards
  env:
    LOGFIRE_TOKEN: ${{ secrets.LOGFIRE_TOKEN }}
    LOGFIRE_ORGANIZATION: my-org
    LOGFIRE_PROJECT: production
  run: |
    for f in integrations/*/overview.yaml; do
      logfire-cli dashboards import "$f"
    done
```
