# Eval Metric Model

The evaluation model includes both quality and operational metrics.

## Representative metrics

- accuracy
- schema_valid_rate
- p95_latency_ms
- mean_cost_estimate
- timeout_rate

## Why these metrics were chosen

The project’s downstream examples support classification, schema compliance, and runtime tradeoffs. These metrics make blocked-release scenarios credible.

## Platform meaning

Metrics are not dashboard decoration. They are used to determine whether a release candidate is promotable.