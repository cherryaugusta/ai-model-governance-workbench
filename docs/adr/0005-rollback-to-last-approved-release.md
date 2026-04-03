# ADR 0005: Roll Back to a Previously Approved Compatible Release

## Status

Accepted

## Context

Rollback is necessary for incident mitigation and operational recovery. Reverting to an arbitrary historical state would be unsafe.

## Decision

Rollback targets must be previously approved compatible releases.

## Consequences

Benefits:
- stronger operational safety
- predictable recovery behavior
- better audit story

Tradeoffs:
- target resolution logic is more complex
- some historical releases are intentionally ineligible

## Rationale

Rollback should restore trust, not introduce another uncontrolled change.