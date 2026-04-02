from apps.audits.models import AuditEvent


def log_audit_event(
    entity_type,
    entity_id,
    event_type,
    actor_type,
    actor_id,
    payload,
    correlation_id,
):
    return AuditEvent.objects.create(
        entity_type=entity_type,
        entity_id=str(entity_id),
        event_type=event_type,
        actor_type=actor_type,
        actor_id=str(actor_id) if actor_id is not None else "",
        payload=payload or {},
        correlation_id=correlation_id or "",
    )