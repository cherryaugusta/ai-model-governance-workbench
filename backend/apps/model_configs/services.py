from django.core.exceptions import ValidationError
from django.db import transaction

from apps.audits.services import log_audit_event
from apps.core.choices import ActorType, ArtefactStatus


@transaction.atomic
def submit_model_config(model_config, actor, correlation_id):
    if model_config.status == ArtefactStatus.RETIRED:
        raise ValidationError("Retired model configs cannot be submitted.")

    model_config.status = ArtefactStatus.CANDIDATE
    model_config.save(update_fields=["status"])

    log_audit_event(
        entity_type="ModelConfig",
        entity_id=model_config.id,
        event_type="submitted",
        actor_type=ActorType.USER,
        actor_id=actor.id if actor and actor.is_authenticated else None,
        payload={
            "ai_system_id": model_config.ai_system_id,
            "version_label": model_config.version_label,
            "status": model_config.status,
        },
        correlation_id=correlation_id,
    )

    return model_config