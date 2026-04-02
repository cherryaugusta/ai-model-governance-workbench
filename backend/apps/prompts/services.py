from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audits.services import log_audit_event
from apps.core.choices import ActorType, ArtefactStatus


@transaction.atomic
def submit_prompt_version(prompt_version, actor, correlation_id):
    if prompt_version.status == ArtefactStatus.RETIRED:
        raise ValidationError("Retired prompt versions cannot be submitted.")

    prompt_version.status = ArtefactStatus.CANDIDATE
    prompt_version.save(update_fields=["status"])

    log_audit_event(
        entity_type="PromptVersion",
        entity_id=prompt_version.id,
        event_type="submitted",
        actor_type=ActorType.USER,
        actor_id=actor.id if actor and actor.is_authenticated else None,
        payload={
            "ai_system_id": prompt_version.ai_system_id,
            "version_label": prompt_version.version_label,
            "status": prompt_version.status,
        },
        correlation_id=correlation_id,
    )

    return prompt_version