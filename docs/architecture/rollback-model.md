# Rollback Model

Rollback is a first-class recovery mechanism, not an afterthought.

## Why rollback exists

AI release safety is incomplete without a reliable path to restore a previously known-good configuration. Evaluation alone does not eliminate operational risk.

Rollback provides:
- mitigation during incidents
- restoration after quality regressions
- recovery from latency or cost breaches
- defensible change safety posture

## Rollback target rules

Rollback should restore a candidate that is:

- previously approved
- compatible with the system
- not the currently active release
- not retired
- suitable as a last-known-good target

## Rollback workflow

1. Incident or operator identifies the need to revert.
2. Platform resolves the eligible rollback target.
3. Current active release is displaced.
4. Previous compatible release becomes active.
5. Rollback record is stored.
6. Audit events capture the transition.

## Data model

Rollback behavior is represented through:
- `RollbackRecord`
- release state changes
- associated incident context where applicable
- audit evidence

## UX posture

Rollback should be visible as a governed action:
- explicit rollback availability on release detail
- reason code and operator comment
- visible restored candidate
- audit evidence after completion

## Portfolio significance

Including rollback as a first-class model makes the project read as serious release management rather than simple approval workflow tooling.