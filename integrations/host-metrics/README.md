# Host Metrics Integration

Monitor host-level system metrics using OpenTelemetry's Host Metrics Receiver.

## Overview

This integration provides dashboards for monitoring:

- CPU utilization (user, system, idle, iowait)
- Memory usage (used, free, cached, buffered)
- Disk I/O (read/write bytes, operations)
- Network I/O (bytes sent/received, packets, errors)
- Filesystem usage (disk space by mount point)

## Prerequisites

- OpenTelemetry Collector with Host Metrics Receiver
- Pydantic Logfire account with metrics ingestion enabled

## Collector Configuration

Deploy the OpenTelemetry Collector with the `hostmetricsreceiver`. See
`collector.yaml` for a complete configuration example.

### Minimum Configuration

```yaml
receivers:
  hostmetrics:
    collection_interval: 30s
    scrapers:
      cpu:
      memory:
      disk:
      network:
      filesystem:

exporters:
  otlp:
    endpoint: "https://logfire-ingest.pydantic.dev"
    headers:
      Authorization: "Bearer ${LOGFIRE_TOKEN}"

service:
  pipelines:
    metrics:
      receivers: [hostmetrics]
      exporters: [otlp]
```

## Metrics

This integration uses the following OpenTelemetry semantic convention metrics:

| Metric | Type | Description |
| ------- | ---- | ----------- |
| `system.cpu.utilization` | Gauge | CPU utilization (0-1) |
| `system.memory.usage` | Gauge | Memory usage in bytes |
| `system.memory.utilization` | Gauge | Memory utilization (0-1) |
| `system.disk.io` | Counter | Disk I/O bytes |
| `system.disk.operations` | Counter | Disk I/O operations |
| `system.network.io` | Counter | Network I/O bytes |
| `system.network.packets` | Counter | Network packets |
| `system.filesystem.usage` | Gauge | Filesystem usage bytes |
| `system.filesystem.utilization` | Gauge | Filesystem utilization (0-1) |

## Dashboard

The `overview.yaml` dashboard provides:

1. **CPU Overview**: Per-core utilization over time with state breakdown
2. **Memory Overview**: Usage breakdown by type (used, cached, buffered, free)
3. **Disk I/O**: Read/write throughput and IOPS
4. **Network I/O**: Bytes and packets by interface
5. **Filesystem Usage**: Disk space utilization by mount point

### Installation

```bash
logfire-cli dashboards import integrations/host-metrics/overview.yaml
```

## Alerts

Common alert thresholds to consider:

| Condition | Warning | Critical |
| --------- | ------- | -------- |
| CPU Utilization | > 80% | > 95% |
| Memory Utilization | > 80% | > 95% |
| Filesystem Utilization | > 80% | > 95% |
| Disk I/O Wait | > 20% | > 50% |

## Troubleshooting

### No Metrics Appearing

1. Verify the collector is running: `systemctl status otelcol`
2. Check collector logs for errors
3. Verify LOGFIRE_TOKEN is set correctly
4. Test connectivity to Logfire endpoint

### Missing CPU States

The Host Metrics Receiver may report different CPU states depending on the OS:

- Linux: user, system, idle, iowait, irq, softirq, nice, steal
- Windows: user, system, idle, interrupt, dpc
- macOS: user, system, idle, nice

### Permission Errors

Some metrics require elevated permissions:

- Filesystem metrics may need read access to mount points
- Network metrics may need CAP_NET_ADMIN on Linux
- Disk metrics may need read access to /dev/disk

## References

- [OTel Host Metrics Receiver](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/hostmetricsreceiver)
- [OTel System Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/system/system-metrics/)
