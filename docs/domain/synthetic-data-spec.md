# Synthetic Data Specification

The project uses deterministic synthetic evaluation data to support reproducible governance workflows.

## Data categories

- baseline
- regression
- adversarial
- routing
- rollback validation

## Why synthetic data is appropriate

For a portfolio system, deterministic synthetic data offers:
- reproducibility
- speed
- easier debugging
- lower provider dependency
- clearer storytelling for release-gate behavior

## Expected characteristics

Synthetic cases should still look operationally plausible and should support:
- blocked promotion
- approval queue scenarios
- rollback demonstrations
- incident-linked mitigation stories