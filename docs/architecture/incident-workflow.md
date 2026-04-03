# Incident Workflow

Incidents connect production-like operational feedback to governed release control.

## Incident purpose

The incident model exists to answer:
What should happen when an active AI release causes or contributes to an operational problem?

## Incident data posture

An incident may link to:
- an AI system
- an active release candidate
- operational severity and type
- mitigation and resolution notes

## Severity significance

High and critical active incidents have governance consequences:
- they block new promotions
- they may trigger rollback
- they become part of the audit narrative

## Workflow

1. Incident is opened against a system or release.
2. Operators investigate and classify severity.
3. If needed, rollback is triggered.
4. Resolution notes are recorded.
5. Incident transitions through mitigation and closure states.
6. Audit trail preserves the sequence.

## Why incidents belong in this platform

Without incidents, release governance stops at promotion time. With incidents, the system models the full operational feedback loop:
- release
- observe
- detect issue
- mitigate
- recover
- audit

That loop is part of the project’s core value proposition.