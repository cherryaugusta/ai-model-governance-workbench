# ADR 0002: Treat Prompts and Model Configs as Versioned Artefacts

## Status

Accepted

## Context

AI changes are often shipped through prompts and runtime settings rather than only through code deployments. The platform must model those as governed release inputs.

## Decision

Store prompts and model configurations as versioned, reviewable artefacts with lifecycle state.

## Consequences

Benefits:
- traceable AI behavior changes
- reviewable artefact history
- clearer release provenance
- cleaner release candidate assembly

Tradeoffs:
- more explicit modelling than inline configuration
- requires version discipline

## Rationale

This decision is central to the platform identity. Without it, the project would read as a generic dashboard instead of a governed AI release workbench.