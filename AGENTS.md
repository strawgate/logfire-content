# Agent Guidelines: Logfire Content

This document provides guidelines for AI agents working on this repository.

## Project Overview

**logfire-content** is a repository containing:

1. **logfire-cli**: A Python CLI for managing Pydantic Logfire dashboards
2. **Perses Dashboard Content**: Pre-built dashboards for common
   infrastructure monitoring
3. **Documentation**: Query references and LLM generation guides for Logfire
   dashboards

## Development Guide

@./DEVELOPING.md

## Dashboard Format

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
                  query: "SELECT time_bucket($resolution, start_timestamp) AS x,
                    ..."
```

## Logfire Query Reference

### Tables

|Table|Use Case|
|---|---|
|`records`|Spans, logs, traces|
|`metrics`|OTel metrics (counters, gauges, histograms)|

### Key Fields - `records`

|Field|Type|Description|
|---|---|---|
|`start_timestamp`|timestamp|When span started|
|`duration`|interval|Span duration|
|`span_name`|string|Operation name|
|`level`|string|Log level|
|`message`|string|Log message|
|`attributes`|jsonb|All OTel attributes|
|`trace_id`|string|Trace identifier|
|`span_id`|string|Span identifier|

### Key Fields - `metrics`

|Field|Type|Description|
|---|---|---|
|`recorded_timestamp`|timestamp|When metric was recorded|
|`metric_name`|string|e.g., `system.cpu.utilization`|
|`scalar_value`|double|For counters/gauges|
|`histogram_count`|int|For histograms|
|`histogram_sum`|double|For histograms|
|`attributes`|jsonb|All OTel attributes|

### Special Variables

|Variable|Description|
|---|---|
|`$resolution`|Auto-calculated time bucket (required for time series)|

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

|Kind|Use Case|Key Options|
|---|---|---|
<!-- markdownlint-disable MD013 -->
|`TimeSeriesChart`|Line/area over time|`legend.position`, `visual.connectNulls`, `yAxis.format`|
<!-- markdownlint-enable MD013 -->
|`StatChart`|Single big number|`calculation`, `format`, `thresholds`, `sparkline`|
|`GaugeChart`|Gauge/meter|`calculation`, `format`, `thresholds`, `max`|
|`BarChart`|Bar charts|`calculation`, `format`, `orientation`|
|`Table`|Tabular data|`columnSettings`|
|`Markdown`|Static text|`text`|
