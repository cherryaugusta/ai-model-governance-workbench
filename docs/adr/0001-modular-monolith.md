# ADR 0001: Use a Modular Monolith

## Status

Accepted

## Context

The project needs strong domain boundaries across systems, prompts, model configs, releases, evals, approvals, incidents, audits, and observability. It also needs to remain implementable and explainable as a portfolio project.

## Decision

Use a modular monolith with Django apps and a React frontend.

## Consequences

Benefits:
- strong logical separation
- lower integration overhead than microservices
- easier local development and testing
- simpler transactional workflows across release, approval, and rollback logic

Tradeoffs:
- not independently deployable by domain
- scale boundaries are logical rather than service-level

## Rationale

For this project, domain clarity matters more than distributed deployment complexity. A modular monolith keeps the architecture serious without overbuilding.