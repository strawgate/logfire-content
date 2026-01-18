# Perses Panel Types

Logfire dashboards use [Perses](https://perses.dev/) panels. This document describes the available panel types and their configuration options.

## TimeSeriesChart

Displays time series data as line or area charts.

### Basic Example

```yaml
MyPanel:
  kind: Panel
  spec:
    display:
      name: "Request Rate"
      description: "Requests per second over time"
    plugin:
      kind: TimeSeriesChart
      spec:
        legend:
          position: bottom  # bottom, right, hidden
          mode: table       # list, table
        yAxis:
          format:
            unit: requests/sec
          min: 0
        visual:
          lineWidth: 1
          areaOpacity: 0      # 0-1, 0 for lines, >0 for area
          connectNulls: false
          stack: none         # none, all, percent
    queries:
      - kind: TimeSeriesQuery
        spec:
          plugin:
            kind: LogfireTimeSeriesQuery
            spec:
              query: |
                SELECT
                  time_bucket($resolution, start_timestamp) AS x,
                  count(1) / EXTRACT(EPOCH FROM $resolution) AS y
                FROM records
                GROUP BY x
                ORDER BY x
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `legend.position` | string | Legend position: `bottom`, `right`, `hidden` |
| `legend.mode` | string | Legend display: `list`, `table` |
| `yAxis.format.unit` | string | Unit for Y-axis values |
| `yAxis.min` | number | Minimum Y-axis value |
| `yAxis.max` | number | Maximum Y-axis value |
| `visual.lineWidth` | number | Line width in pixels |
| `visual.areaOpacity` | number | Area fill opacity (0-1) |
| `visual.connectNulls` | boolean | Connect lines across null values |
| `visual.stack` | string | Stacking mode: `none`, `all`, `percent` |

### Common Units

- Time: `seconds`, `milliseconds`, `nanoseconds`
- Rate: `requests/sec`, `ops/sec`, `bytes/sec`
- Size: `bytes`, `kilobytes`, `megabytes`, `gigabytes`
- Percentage: `percent`, `percentunit` (0-1 scale)

## StatChart

Displays a single large number with optional sparkline.

### Basic Example

```yaml
CPUStat:
  kind: Panel
  spec:
    display:
      name: "CPU Usage"
    plugin:
      kind: StatChart
      spec:
        calculation: last  # last, first, mean, sum, min, max
        format:
          unit: percent
        thresholds:
          mode: absolute  # absolute, percentage
          steps:
            - value: 0
              color: green
            - value: 80
              color: yellow
            - value: 95
              color: red
        sparkline:
          show: true
          width: 1
          color: "#3274D9"
    queries:
      - kind: TimeSeriesQuery
        spec:
          plugin:
            kind: LogfireTimeSeriesQuery
            spec:
              query: |
                SELECT
                  time_bucket($resolution, recorded_timestamp) AS x,
                  avg(scalar_value) * 100 AS y
                FROM metrics
                WHERE metric_name = 'system.cpu.utilization'
                GROUP BY x
                ORDER BY x
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `calculation` | string | Value calculation: `last`, `first`, `mean`, `sum`, `min`, `max` |
| `format.unit` | string | Display unit |
| `thresholds.mode` | string | Threshold mode: `absolute`, `percentage` |
| `thresholds.steps` | array | Color steps with value and color |
| `sparkline.show` | boolean | Show sparkline chart |
| `sparkline.width` | number | Sparkline line width |
| `sparkline.color` | string | Sparkline color (hex) |

## GaugeChart

Displays a gauge/meter visualization.

### Basic Example

```yaml
MemoryGauge:
  kind: Panel
  spec:
    display:
      name: "Memory"
    plugin:
      kind: GaugeChart
      spec:
        calculation: last
        format:
          unit: percent
        max: 100
        thresholds:
          steps:
            - value: 0
              color: green
            - value: 80
              color: yellow
            - value: 95
              color: red
    queries:
      - kind: TimeSeriesQuery
        spec:
          plugin:
            kind: LogfireTimeSeriesQuery
            spec:
              query: |
                SELECT avg(scalar_value) * 100 AS value
                FROM metrics
                WHERE metric_name = 'system.memory.utilization'
                  AND recorded_timestamp > now() - interval '5 minutes'
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `calculation` | string | Value calculation method |
| `format.unit` | string | Display unit |
| `max` | number | Maximum gauge value |
| `thresholds.steps` | array | Color steps |

## BarChart

Displays data as bar charts.

### Basic Example

```yaml
RequestsByEndpoint:
  kind: Panel
  spec:
    display:
      name: "Requests by Endpoint"
    plugin:
      kind: BarChart
      spec:
        calculation: sum
        format:
          unit: short
        orientation: horizontal  # horizontal, vertical
        sort: descending         # ascending, descending, none
    queries:
      - kind: TimeSeriesQuery
        spec:
          plugin:
            kind: LogfireTimeSeriesQuery
            spec:
              query: |
                SELECT
                  attributes->>'http.route' AS x,
                  count(1) AS y
                FROM records
                WHERE span_name LIKE 'HTTP%'
                  AND start_timestamp > now() - interval '1 hour'
                GROUP BY x
                ORDER BY y DESC
                LIMIT 10
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `calculation` | string | Value calculation |
| `format.unit` | string | Display unit |
| `orientation` | string | Bar orientation: `horizontal`, `vertical` |
| `sort` | string | Sort order: `ascending`, `descending`, `none` |

## Table

Displays tabular data.

### Basic Example

```yaml
TopEndpoints:
  kind: Panel
  spec:
    display:
      name: "Top Endpoints"
    plugin:
      kind: Table
      spec:
        columnSettings:
          endpoint:
            name: Endpoint
            width: 300
          requests:
            name: Requests
            format:
              unit: short
          avg_ms:
            name: Avg Latency
            format:
              unit: milliseconds
          error_rate:
            name: Error Rate
            format:
              unit: percent
    queries:
      - kind: TimeSeriesQuery
        spec:
          plugin:
            kind: LogfireTimeSeriesQuery
            spec:
              query: |
                SELECT
                  attributes->>'http.route' AS endpoint,
                  count(1) AS requests,
                  avg(EXTRACT(EPOCH FROM duration) * 1000) AS avg_ms,
                  count(CASE WHEN attributes->>'http.status_code' LIKE '5%' THEN 1 END)::float /
                    NULLIF(count(1), 0) * 100 AS error_rate
                FROM records
                WHERE span_name LIKE 'HTTP%'
                  AND start_timestamp > now() - interval '1 hour'
                GROUP BY endpoint
                ORDER BY requests DESC
                LIMIT 20
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `columnSettings.<col>.name` | string | Column display name |
| `columnSettings.<col>.width` | number | Column width in pixels |
| `columnSettings.<col>.format.unit` | string | Value format unit |
| `columnSettings.<col>.hidden` | boolean | Hide column |

## Markdown

Displays static markdown text.

### Basic Example

```yaml
Instructions:
  kind: Panel
  spec:
    display:
      name: "Instructions"
    plugin:
      kind: Markdown
      spec:
        text: |
          ## Dashboard Guide

          This dashboard shows key metrics for your application:

          - **CPU**: System CPU utilization
          - **Memory**: Memory usage and pressure
          - **Network**: Traffic in/out

          ### Alerts

          Set up alerts when:
          - CPU > 80% for 5 minutes
          - Memory > 90% for 5 minutes
```

### Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `text` | string | Markdown content |

## Layout Configuration

Panels are positioned using a grid layout.

### Grid Layout

```yaml
layouts:
  - kind: Grid
    spec:
      display:
        title: "Overview"  # Optional section title
      items:
        - x: 0       # Column position (0-23)
          y: 0       # Row position
          width: 12  # Width in columns (out of 24)
          height: 6  # Height in rows
          content:
            $ref: "#/spec/panels/MyPanel"
```

### Layout Tips

- Grid is 24 columns wide
- Height is in rows (typically 1 row = ~40px)
- Use `$ref` to reference panels defined in `spec.panels`
- Position panels left-to-right, top-to-bottom
- Common widths: 6 (quarter), 8 (third), 12 (half), 24 (full)
- Common heights: 4-6 (stats), 8-10 (charts), 12+ (tables)

### Multiple Sections

```yaml
layouts:
  - kind: Grid
    spec:
      display:
        title: "Overview"
      items:
        - x: 0
          y: 0
          width: 24
          height: 6
          content:
            $ref: "#/spec/panels/SummaryPanel"
  - kind: Grid
    spec:
      display:
        title: "Details"
      items:
        - x: 0
          y: 0
          width: 12
          height: 8
          content:
            $ref: "#/spec/panels/DetailPanel1"
        - x: 12
          y: 0
          width: 12
          height: 8
          content:
            $ref: "#/spec/panels/DetailPanel2"
```
