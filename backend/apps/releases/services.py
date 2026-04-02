from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audits.services import log_audit_event
from apps.core.choices import ActorType, ReleaseCandidateStatus

from .models import ReleaseCandidate


def create_release_candidate_snapshot(candidate: ReleaseCandidate) -> dict:
    return {
        "submitted_at": timezone.now().isoformat(),
        "ai_system": {
            "id": candidate.ai_system.id,
            "name": candidate.ai_system.name,
            "slug": candidate.ai_system.slug,
            "risk_tier": candidate.ai_system.risk_tier,
            "status": candidate.ai_system.status,
        },
        "prompt_version": {
            "id": candidate.prompt_version.id,
            "name": candidate.prompt_version.name,
            "version_label": candidate.prompt_version.version_label,
            "status": candidate.prompt_version.status,
            "schema_version": candidate.prompt_version.schema_version,
            "template_text": candidate.prompt_version.template_text,
            "input_contract": candidate.prompt_version.input_contract,
            "output_contract": candidate.prompt_version.output_contract,
        },
        "model_config": {
            "id": candidate.model_config.id,
            "version_label": candidate.model_config.version_label,
            "status": candidate.model_config.status,
            "provider_name": candidate.model_config.provider_name,
            "model_name": candidate.model_config.model_name,
            "temperature": str(candidate.model_config.temperature),
            "max_tokens": candidate.model_config.max_tokens,
            "top_p": str(candidate.model_config.top_p),
            "timeout_ms": candidate.model_config.timeout_ms,
            "routing_policy": candidate.model_config.routing_policy,
            "fallback_policy": candidate.model_config.fallback_policy,
            "cost_budget_per_run": str(candidate.model_config.cost_budget_per_run),
        },
        "eval_dataset_ids": candidate.eval_dataset_ids,
    }


def submit_release_candidate(
    candidate: ReleaseCandidate,
    actor,
    correlation_id: str,
) -> ReleaseCandidate:
    if candidate.status != ReleaseCandidateStatus.DRAFT:
        raise ValidationError("Only draft release candidates can be submitted.")

    candidate.config_snapshot = create_release_candidate_snapshot(candidate)
    candidate.status = ReleaseCandidateStatus.PENDING_EVAL
    candidate.save()

    log_audit_event(
        entity_type="ReleaseCandidate",
        entity_id=candidate.id,
        event_type="submitted",
        actor_type=ActorType.USER,
        actor_id=actor.id if actor and actor.is_authenticated else None,
        payload={
            "name": candidate.name,
            "status": candidate.status,
            "ai_system_id": candidate.ai_system_id,
            "prompt_version_id": candidate.prompt_version_id,
            "model_config_id": candidate.model_config_id,
        },
        correlation_id=correlation_id,
    )

    return candidate
