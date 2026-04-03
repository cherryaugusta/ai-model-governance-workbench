# System Overview

AI Model Governance Workbench is a modular monolith for governed release management of AI-enabled systems. It is positioned as an internal control plane rather than an end-user AI experience.

## Problem framing

The platform exists to manage risky AI changes safely. The key problem is not prompt experimentation. The key problem is controlled lifecycle management for prompt and model changes that affect production behavior.

The platform treats prompts and model configurations as governed artefacts. It assembles immutable release candidates, runs deterministic evaluations, enforces risk-tier approval policy, blocks unsafe promotion, connects incidents to rollback, and records an immutable audit trail.

## Architectural shape

- modular monolith
- Django + DRF backend
- React + TypeScript + Vite frontend
- PostgreSQL as system of record
- Redis as Celery broker/result backend
- Celery for async evaluation-related jobs
- Docker Compose for local development

## Core workflow

1. Register an AI-enabled system.
2. Create prompt and model configuration versions.
3. Assemble a release candidate from those artefacts.
4. Freeze an immutable release snapshot on submission.
5. Run deterministic eval suites.
6. Block or allow promotion based on thresholds and approvals.
7. Promote a validated candidate to active release.
8. Open incidents against active systems or releases.
9. Roll back to a previously approved compatible release.
10. Preserve lifecycle evidence in immutable audit events.

## Backend boundaries

- `core` provides shared middleware, logging, and common platform utilities
- `accounts` supports authenticated users and reviewer identities
- `systems` models the governed inventory of AI-enabled systems
- `prompts` manages versioned prompt artefacts
- `model_configs` manages versioned runtime/model artefacts
- `releases` manages immutable release candidates, promotion, and rollback
- `evals` manages datasets, cases, runs, and threshold results
- `approvals` manages risk-tier review policy and decisions
- `incidents` manages operational incidents and mitigation lifecycle
- `audits` manages immutable audit events
- `observability` aggregates metrics and execution logs
- `health` exposes liveness, readiness, and dependency checks

## Frontend posture

The frontend is intentionally control-plane oriented. It emphasizes lifecycle evidence rather than visual decoration.

Primary views:
- systems registry
- system detail
- release candidate detail
- eval dashboard
- approval queue
- incident dashboard
- audit timeline
- prompt detail
- model config detail

## Design principles

- prompts and model configs are first-class governed artefacts
- release candidates are immutable after submission
- promotion is a business transition, not a generic status edit
- rollback is a first-class recovery workflow
- incidents are connected to release history and blocking logic
- audit history is append-only
- deterministic evaluation is more important than flashy inference

## Portfolio significance

This repository is designed to read as platform-grade internal tooling for safe AI change management. It demonstrates domain modelling, workflow APIs, evaluation-backed release control, incident-linked rollback, and auditable operations.