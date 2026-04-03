# Evaluation Design

The evaluation system is designed to support release safety rather than leaderboard-style benchmarking.

## Role of evals

Evaluations answer a release question:
Can this candidate safely replace the current active release?

They are not decorative metrics. They directly influence promotion eligibility.

## Dataset categories

The repository uses deterministic synthetic datasets across multiple scenarios:

- baseline
- regression
- adversarial
- routing
- rollback validation

These categories let the platform simulate:
- quality regressions
- schema failures
- latency and cost issues
- failure handling
- rollback readiness

## Metrics

Representative metrics include:
- accuracy
- schema_valid_rate
- p95_latency_ms
- mean_cost_estimate
- timeout_rate
- fallback success posture where applicable

## Threshold posture

Candidates are evaluated against deterministic thresholds rather than subjective review alone.

Examples:
- minimum quality floor
- maximum latency envelope
- maximum cost envelope
- schema validity expectations

## Comparisons

A candidate can be compared against:
- static threshold baseline
- current active release
- last-known-good release

This gives the platform meaningful regression language rather than isolated scores.

## Storage model

Eval state is preserved in:
- `EvalDataset`
- `EvalCase`
- `EvalRun`
- `EvalRunCaseResult`
- `ModelExecutionLog`

Completed runs store:
- summary metrics
- threshold breakdown
- case-level outcomes
- baseline comparisons

## Why deterministic evaluation is correct here

For a portfolio project, deterministic evaluation has strong benefits:
- reproducible outcomes
- faster iteration
- simpler debugging
- less dependence on live providers
- clearer release-gate narratives