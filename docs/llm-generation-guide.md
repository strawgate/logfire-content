# LLM Dashboard Generation Guide

This guide explains how to prompt LLMs to generate valid Logfire dashboards.

## Prompt Template

Use this template when asking an LLM to generate a dashboard:

```markdown
Generate a Perses dashboard YAML for monitoring {technology} in Pydantic Logfire.

## Logfire Query Plugin

Use `LogfireTimeSeriesQuery` with SQL queries:

queries:
  - kind: TimeSeriesQuery
    spec:
      plugin:
        kind: LogfireTimeSeriesQuery
        spec:
          query: "SELECT time_bucket($resolution, recorded_timestamp) AS x, ..."

## Available Data

{describe available metrics, spans, or logs}

## Requirements

- Use `$resolution` for all time series queries
- Query from `metrics` table for OTel metrics
- Query from `records` table for spans/logs
- Use `attributes->>'key'` for JSON attribute access
- Include thresholds for stat/gauge panels
- Return valid Perses YAML format

## Example Panel

{include an example panel from this repository}
```

## Key Context to Provide

### 1. Data Schema

Tell the LLM what data is available:

```markdown
## Available Metrics

| Metric | Type | Attributes |
|--------|------|------------|
| `http.server.request.duration` | histogram | method, route, status_code |
| `http.server.active_requests` | gauge | method |
| `db.client.operation.duration` | histogram | db.system, db.operation |

## Available Spans

| Span Name | Key Attributes |
|-----------|----------------|
| `HTTP GET /api/*` | http.method, http.route, http.status_code |
| `PostgreSQL query` | db.statement, db.operation |
```

### 2. Query Patterns

Include examples of valid queries:

```markdown
## Query Patterns

Time series with rate:
SELECT
  time_bucket($resolution, start_timestamp) AS x,
  count(1) / EXTRACT(EPOCH FROM $resolution) AS y
FROM records
GROUP BY x
ORDER BY x

Single stat:
SELECT count(1) AS value
FROM records
WHERE start_timestamp > now() - interval '5 minutes'

Table:
SELECT col1, col2, count(1) AS count
FROM records
GROUP BY col1, col2
LIMIT 10
```

### 3. Panel Type Examples

Show the exact YAML structure for each panel type:

```yaml
# TimeSeriesChart example
MyChart:
  kind: Panel
  spec:
    display:
      name: "Chart Title"
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
                SELECT ... AS x, ... AS y
                FROM ...
                GROUP BY x
                ORDER BY x
```

## Common Mistakes to Avoid

### 1. Missing `$resolution`

```yaml
# WRONG - missing $resolution
query: |
  SELECT
    date_trunc('minute', start_timestamp) AS x,  # Wrong!
    count(1) AS y
  FROM records
  GROUP BY x

# CORRECT
query: |
  SELECT
    time_bucket($resolution, start_timestamp) AS x,
    count(1) AS y
  FROM records
  GROUP BY x
  ORDER BY x
```

### 2. Wrong Query Plugin

```yaml
# WRONG - PrometheusTimeSeriesQuery doesn't exist in Logfire
plugin:
  kind: PrometheusTimeSeriesQuery
  spec:
    expr: "rate(http_requests_total[5m])"

# CORRECT - Use LogfireTimeSeriesQuery with SQL
plugin:
  kind: LogfireTimeSeriesQuery
  spec:
    query: |
      SELECT
        time_bucket($resolution, start_timestamp) AS x,
        count(1) / EXTRACT(EPOCH FROM $resolution) AS y
      FROM records
      GROUP BY x
```

### 3. Missing ORDER BY

```yaml
# WRONG - missing ORDER BY
query: |
  SELECT
    time_bucket($resolution, start_timestamp) AS x,
    count(1) AS y
  FROM records
  GROUP BY x  # Missing ORDER BY x!

# CORRECT
query: |
  SELECT
    time_bucket($resolution, start_timestamp) AS x,
    count(1) AS y
  FROM records
  GROUP BY x
  ORDER BY x  # Required for time series
```

### 4. Incorrect Attribute Access

```yaml
# WRONG - using dot notation
WHERE attributes.http.method = 'GET'

# CORRECT - using PostgreSQL JSONB operators
WHERE attributes->>'http.method' = 'GET'
```

### 5. Wrong Column Names

```yaml
# WRONG - using 'time' instead of 'x'
SELECT
  time_bucket($resolution, start_timestamp) AS time,
  count(1) AS value
FROM records

# CORRECT - use 'x' for time, 'y' for value, 'series' for grouping
SELECT
  time_bucket($resolution, start_timestamp) AS x,
  count(1) AS y
FROM records
```

## Validation Workflow

After LLM generates a dashboard:

1. **YAML Parse** - Ensure valid YAML syntax
2. **Schema Check** - Validate against Perses schema with `percli lint`
3. **Query Check** - Manually review SQL queries for correctness
4. **Push to Logfire** - `logfire-cli push dashboard.yaml`
5. **Visual Check** - Verify panels render correctly in Logfire UI

## Example: Full Generation Prompt

```markdown
Generate a Perses dashboard YAML for monitoring a FastAPI application in Logfire.

## Data Available

Spans from FastAPI auto-instrumentation:
- Span name pattern: "HTTP {method} {route}"
- Attributes: http.method, http.route, http.status_code, http.response.body.size

## Dashboard Requirements

1. Request rate over time (by method)
2. Error rate (5xx responses)
3. P95 latency
4. Top 10 slowest endpoints table
5. Current active requests stat

## Query Plugin Format

queries:
  - kind: TimeSeriesQuery
    spec:
      plugin:
        kind: LogfireTimeSeriesQuery
        spec:
          query: "..."

## Example Time Series Query

SELECT
  time_bucket($resolution, start_timestamp) AS x,
  attributes->>'http.method' AS series,
  count(1) / EXTRACT(EPOCH FROM $resolution) AS y
FROM records
WHERE span_name LIKE 'HTTP%'
GROUP BY x, series
ORDER BY x

Return the complete dashboard YAML with proper layout.
```

## Tips for Better Results

1. **Be Specific** - Provide exact metric names, span names, attribute keys
2. **Show Examples** - Include working query examples
3. **Specify Format** - Request specific panel types and layouts
4. **Iterate** - Review output and ask for corrections
5. **Validate** - Always validate with `logfire-cli lint` before pushing
