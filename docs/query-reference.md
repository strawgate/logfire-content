# Logfire Query Reference

Logfire uses a custom query plugin called `LogfireTimeSeriesQuery` that executes SQL against your telemetry data.

## Tables

| Table | Use Case |
|-------|----------|
| `records` | Spans, logs, traces |
| `metrics` | OTel metrics (counters, gauges, histograms) |

## Records Table

The `records` table contains all spans and logs from your application.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `start_timestamp` | timestamp | When the span/log started |
| `end_timestamp` | timestamp | When the span ended |
| `duration` | interval | Span duration |
| `span_name` | string | Operation name |
| `level` | string | Log level (info, warn, error, etc.) |
| `message` | string | Log message |
| `attributes` | jsonb | All OpenTelemetry attributes |
| `trace_id` | string | Trace identifier |
| `span_id` | string | Span identifier |
| `parent_span_id` | string | Parent span identifier |
| `service_name` | string | Service name |
| `kind` | string | Span kind (client, server, internal, etc.) |

### Accessing Attributes

Use the `->>'key'` operator to access string values from attributes:

```sql
attributes->>'http.method'
attributes->>'http.status_code'
attributes->>'user.id'
```

Use `->` for nested access or to get JSON values:

```sql
attributes->'http.request.header'->>'content-type'
```

## Metrics Table

The `metrics` table contains OpenTelemetry metrics.

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `recorded_timestamp` | timestamp | When the metric was recorded |
| `metric_name` | string | Metric name (e.g., `system.cpu.utilization`) |
| `scalar_value` | double | Value for counters/gauges |
| `histogram_count` | int | Count for histograms |
| `histogram_sum` | double | Sum for histograms |
| `histogram_min` | double | Minimum for histograms |
| `histogram_max` | double | Maximum for histograms |
| `attributes` | jsonb | All OpenTelemetry attributes |
| `unit` | string | Metric unit |

## Special Variables

| Variable | Description |
|----------|-------------|
| `$resolution` | Auto-calculated time bucket based on dashboard time range |

The `$resolution` variable is **required** for all time series queries. It automatically adjusts based on the selected time range.

## Query Patterns

### Time Series (Line Chart)

Use for `TimeSeriesChart` panels:

```sql
SELECT
  time_bucket($resolution, start_timestamp) AS x,
  count(1) AS y
FROM records
WHERE span_name = 'HTTP GET'
GROUP BY x
ORDER BY x
```

### Time Series with Series Breakdown

Create multiple lines based on a dimension:

```sql
SELECT
  time_bucket($resolution, recorded_timestamp) AS x,
  attributes->>'service.name' AS series,
  avg(scalar_value) AS y
FROM metrics
WHERE metric_name = 'system.cpu.utilization'
GROUP BY x, series
ORDER BY x
```

### Stat/Gauge (Single Value)

Use for `StatChart` or `GaugeChart` panels. No time bucket needed:

```sql
SELECT avg(scalar_value) * 100 AS value
FROM metrics
WHERE metric_name = 'system.memory.utilization'
  AND recorded_timestamp > now() - interval '5 minutes'
```

### Stat with Sparkline

For stats with sparkline, return a time series:

```sql
SELECT
  time_bucket($resolution, recorded_timestamp) AS x,
  avg(scalar_value) * 100 AS y
FROM metrics
WHERE metric_name = 'system.cpu.utilization'
GROUP BY x
ORDER BY x
```

### Table Query

Use for `Table` panels:

```sql
SELECT
  attributes->>'http.route' AS route,
  count(1) AS requests,
  avg(duration) AS avg_duration,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY duration) AS p95_duration
FROM records
WHERE span_name LIKE 'HTTP%'
  AND start_timestamp > now() - interval '1 hour'
GROUP BY route
ORDER BY requests DESC
LIMIT 10
```

### Rate Calculations

Calculate per-second rates from counters:

```sql
SELECT
  time_bucket($resolution, recorded_timestamp) AS x,
  sum(scalar_value) / EXTRACT(EPOCH FROM $resolution) AS y
FROM metrics
WHERE metric_name = 'http.server.request.count'
GROUP BY x
ORDER BY x
```

### Histogram Percentiles

Calculate percentiles from histogram data:

```sql
SELECT
  time_bucket($resolution, recorded_timestamp) AS x,
  histogram_sum / NULLIF(histogram_count, 0) AS avg_value,
  histogram_max AS max_value
FROM metrics
WHERE metric_name = 'http.server.request.duration'
GROUP BY x
ORDER BY x
```

## Common Filter Patterns

### By Service

```sql
WHERE attributes->>'service.name' = 'api-server'
```

### By Environment

```sql
WHERE attributes->>'deployment.environment' = 'production'
```

### By HTTP Status

```sql
WHERE attributes->>'http.status_code' LIKE '5%'  -- 5xx errors
```

### By Log Level

```sql
WHERE level IN ('error', 'fatal')
```

### Time Range

```sql
WHERE start_timestamp > now() - interval '1 hour'
```

## Performance Tips

1. **Always filter by time** - Use time range filters in WHERE clauses
2. **Limit results** - Use LIMIT for table queries
3. **Index-friendly filters** - Filter on indexed columns first (timestamp, metric_name, span_name)
4. **Avoid SELECT *** - Only select needed columns
5. **Use $resolution** - Let the dashboard calculate optimal bucket size

## Examples by Panel Type

### TimeSeriesChart - Request Rate

```sql
SELECT
  time_bucket($resolution, start_timestamp) AS x,
  attributes->>'http.method' AS series,
  count(1) / EXTRACT(EPOCH FROM $resolution) AS y
FROM records
WHERE span_name LIKE 'HTTP%'
GROUP BY x, series
ORDER BY x
```

### StatChart - Error Rate

```sql
SELECT
  time_bucket($resolution, start_timestamp) AS x,
  count(CASE WHEN attributes->>'http.status_code' LIKE '5%' THEN 1 END)::float /
    NULLIF(count(1), 0) * 100 AS y
FROM records
WHERE span_name LIKE 'HTTP%'
GROUP BY x
ORDER BY x
```

### GaugeChart - Memory Usage

```sql
SELECT
  avg(scalar_value) * 100 AS value
FROM metrics
WHERE metric_name = 'system.memory.utilization'
  AND attributes->>'state' = 'used'
  AND recorded_timestamp > now() - interval '5 minutes'
```

### Table - Top Endpoints

```sql
SELECT
  attributes->>'http.route' AS endpoint,
  count(1) AS requests,
  avg(EXTRACT(EPOCH FROM duration) * 1000) AS avg_ms,
  count(CASE WHEN attributes->>'http.status_code' LIKE '5%' THEN 1 END) AS errors
FROM records
WHERE span_name LIKE 'HTTP%'
  AND start_timestamp > now() - interval '1 hour'
GROUP BY endpoint
ORDER BY requests DESC
LIMIT 20
```
