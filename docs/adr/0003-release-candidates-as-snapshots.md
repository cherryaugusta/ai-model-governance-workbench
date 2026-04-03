# ADR 0003: Model Release Candidates as Immutable Snapshots

## Status

Accepted

## Context

A governed release decision must be attached to a stable set of artefacts. Mutable references alone are insufficient for release safety and auditability.

## Decision

Freeze release candidates as immutable snapshots after submission.

## Consequences

Benefits:
- stable approval target
- stable eval target
- stable promotion evidence
- better auditability

Tradeoffs:
- requires more explicit release modelling
- snapshot generation must be reliable

## Rationale

This is the backbone of controlled release management in the platform.