# ADR 0004: Use Evals as Promotion Gates

## Status

Accepted

## Context

Approval alone is not sufficient for safe AI release. The system must incorporate deterministic quality and operational evidence.

## Decision

Promotion is blocked unless the latest relevant eval posture is passing.

## Consequences

Benefits:
- promotion reflects measurable evidence
- regression protection becomes visible
- blocked promotion becomes explainable

Tradeoffs:
- eval design must stay credible
- simulated runner quality influences platform credibility

## Rationale

This decision makes the platform read as controlled release infrastructure instead of workflow-only tooling.