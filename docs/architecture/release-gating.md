# Release Gating

Promotion in AI Model Governance Workbench is intentionally blocked unless deterministic governance requirements pass.

## Promotion gates

A release candidate may be promoted only when all of the following are true:

- the latest relevant evaluation run passed
- all required approvals for the system risk tier are complete
- no blocking high or critical open incidents exist
- the candidate is in a promotable lifecycle state
- the prompt and model config are still eligible for governed release use

## Blocking reason design

The platform surfaces blocking reasons as explicit user-visible evidence. It does not stop after the first failure. It reports the full blocker set.

Typical blocker categories:
- latest eval failed
- missing required approval
- blocking incident exists
- candidate not submitted
- awaiting eval results
- invalid lifecycle state

## Why deterministic gates matter

The core value of the platform is safe change management. Promotion must not read like a manual status change. It must read like a governed release event.

Deterministic gating provides:
- reproducibility
- auditability
- operator trust
- explainable release behavior

## User experience posture

The release candidate page should make blocked promotion obvious:
- readiness fields
- visible blocker count
- explicit blocker list
- approval completeness state
- latest eval posture
- promote action disabled when blocked

## Operational significance

This design makes the repository read as internal release control infrastructure for AI-enabled systems instead of a generic admin panel.