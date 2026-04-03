# Failure Modes

The repository is designed around the idea that AI changes can fail in multiple ways, not just quality loss.

## Major governed failure modes

### Threshold regression
The candidate fails one or more eval thresholds such as quality, latency, or cost.

### Missing approvals
The candidate passes evals but cannot be promoted because mandatory risk-tier reviews are incomplete.

### Blocking incidents
An unrelated high or critical operational issue is active, so promotion is paused even if the candidate itself looks valid.

### Invalid lifecycle state
A candidate has not passed through required transitions and is therefore not promotable.

### Release incompatibility
Rollback target or promotion state is invalid because the referenced artefact history is incompatible or ineligible.

## Platform response strategy

The system handles these through:
- explicit blocker reporting
- deterministic state checks
- immutable audit evidence
- operational dashboards
- rollback workflows where appropriate

## Why documenting failure modes matters

This project is stronger when it shows what the platform prevents, not only what it enables.