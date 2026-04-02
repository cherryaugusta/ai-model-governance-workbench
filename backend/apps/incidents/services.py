from rest_framework.exceptions import ValidationError

from apps.audits.services import log_audit_event
from apps.core.choices import ActorType, IncidentSeverity, IncidentStatus

from .models import Incident


def blocking_incidents_for_system(ai_system):
    return Incident.objects.filter(
        ai_system=ai_system,
        severity__in=[IncidentSeverity.HIGH, IncidentSeverity.CRITICAL],
        status__in=[
            IncidentStatus.OPEN,
            IncidentStatus.INVESTIGATING,
            IncidentStatus.MITIGATED,
        ],
    )


def open_incident(
    *,
    ai_system,
    release_candidate,
    incident_type: str,
    severity: str,
    summary: str,
    description: str,
    actor,
    correlation_id: str,
) -> Incident:
    incident = Incident.objects.create(
        ai_system=ai_system,
        release_candidate=release_candidate,
        incident_type=incident_type,
        severity=severity,
        status=IncidentStatus.OPEN,
        summary=summary,
        description=description,
        reported_by=actor,
    )

    log_audit_event(
        entity_type="Incident",
        entity_id=incident.id,
        event_type="opened",
        actor_type=ActorType.USER,
        actor_id=actor.id if actor and actor.is_authenticated else None,
        payload={
            "ai_system_id": incident.ai_system_id,
            "release_candidate_id": incident.release_candidate_id,
            "incident_type": incident.incident_type,
            "severity": incident.severity,
            "status": incident.status,
            "summary": incident.summary,
        },
        correlation_id=correlation_id,
    )

    return incident


def resolve_incident(
    incident: Incident,
    actor,
    resolution_notes: str,
    correlation_id: str,
) -> Incident:
    if incident.status in {IncidentStatus.RESOLVED, IncidentStatus.CLOSED}:
        raise ValidationError("Only unresolved incidents can be resolved.")

    incident.status = IncidentStatus.RESOLVED
    incident.resolution_notes = resolution_notes
    incident.save(update_fields=["status", "resolution_notes", "updated_at"])

    log_audit_event(
        entity_type="Incident",
        entity_id=incident.id,
        event_type="resolved",
        actor_type=ActorType.USER,
        actor_id=actor.id if actor and actor.is_authenticated else None,
        payload={
            "ai_system_id": incident.ai_system_id,
            "release_candidate_id": incident.release_candidate_id,
            "severity": incident.severity,
            "status": incident.status,
            "resolution_notes": incident.resolution_notes,
        },
        correlation_id=correlation_id,
    )

    return incident