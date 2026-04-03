# Lifecycle Model

The platform models AI change as a governed lifecycle rather than a loose collection of editable records.

## PromptVersion lifecycle

Prompt versions support reviewable artefact governance.

States:
- `draft`
- `candidate`
- `approved`
- `rejected`
- `retired`

Rules:
- authors can iterate in draft
- submit transitions draft to candidate
- approved prompt versions can be attached to release candidates
- retired prompt versions cannot be reused for new promotion paths

## ModelConfig lifecycle

Model configurations follow the same reviewable artefact posture.

States:
- `draft`
- `candidate`
- `approved`
- `rejected`
- `retired`

Rules:
- runtime parameters are versioned
- fallback and routing policies are governed with the config
- retired model configs are excluded from new governed releases

## ReleaseCandidate lifecycle

Release candidates encode the key governed release workflow.

States:
- `draft`
- `pending_eval`
- `eval_failed`
- `pending_approval`
- `approved`
- `rejected`
- `active`
- `rolled_back`
- `retired`

Rules:
- candidate starts as draft
- submission freezes the immutable snapshot
- evals move the candidate to `eval_failed` or `pending_approval`
- approvals move the candidate to `approved` or `rejected`
- promotion moves an approved candidate to `active`
- rollback moves the active candidate to `rolled_back` and restores a previous compatible release

## Incident lifecycle

Incidents represent operational evidence with mitigation state.

States:
- `open`
- `investigating`
- `mitigated`
- `resolved`
- `closed`

Rules:
- high and critical open incidents block new promotions
- incidents may link directly to a release candidate
- resolved incidents preserve historical evidence without blocking later promotion

## Why this model matters

This lifecycle structure makes the platform more than CRUD:
- lifecycle transitions are explicit
- invalid transitions can be rejected deterministically
- promotion and rollback become defendable business workflows
- auditability is attached to meaningful state changes