from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.approvals.services import all_required_approvals_complete
from apps.audits.services import log_audit_event
from apps.core.choices import ActorType, EvalRunStatus, ReleaseCandidateStatus
from apps.evals.models import EvalRun
from apps.incidents.services import blocking_incidents_for_system

from .models import PromotionEvent, ReleaseCandidate, RollbackRecord


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


def latest_completed_eval_run(candidate: ReleaseCandidate) -> EvalRun | None:
    return (
        candidate.eval_runs.filter(
            status__in=[EvalRunStatus.PASSED, EvalRunStatus.FAILED],
        )
        .order_by("-completed_at", "-created_at")
        .first()
    )


def promotion_blocking_reasons(candidate: ReleaseCandidate) -> list[str]:
    reasons = []

    if candidate.status != ReleaseCandidateStatus.APPROVED:
        reasons.append("candidate_not_approved")

    if not candidate.config_snapshot:
        reasons.append("snapshot_not_created")

    latest_eval = latest_completed_eval_run(candidate)
    if latest_eval is None:
        reasons.append("latest_eval_missing")
    elif latest_eval.status != EvalRunStatus.PASSED:
        reasons.append("latest_eval_failed")

    if not all_required_approvals_complete(candidate):
        reasons.append("required_approvals_incomplete")

    if candidate.prompt_version.status == "retired":
        reasons.append("prompt_version_retired")

    if candidate.model_config.status == "retired":
        reasons.append("model_config_retired")

    if blocking_incidents_for_system(candidate.ai_system).exists():
        reasons.append("blocking_incidents_open")

    return reasons


def rollback_target_for_system(ai_system, exclude_candidate_id: int | None = None) -> ReleaseCandidate | None:
    queryset = ReleaseCandidate.objects.filter(
        ai_system=ai_system,
        status__in=[ReleaseCandidateStatus.APPROVED, ReleaseCandidateStatus.ROLLED_BACK],
    ).exclude(
        prompt_version__status="retired",
    ).exclude(
        model_config__status="retired",
    ).order_by(
        "-updated_at",
        "-created_at",
    )

    if exclude_candidate_id is not None:
        queryset = queryset.exclude(id=exclude_candidate_id)

    return queryset.first()


def rollback_blocking_reasons(candidate: ReleaseCandidate) -> list[str]:
    reasons = []

    if candidate.status != ReleaseCandidateStatus.ACTIVE:
        reasons.append("candidate_not_active")

    target = rollback_target_for_system(candidate.ai_system, exclude_candidate_id=candidate.id)
    if target is None:
        reasons.append("rollback_target_unavailable")

    return reasons


@transaction.atomic
def promote_candidate(
    candidate: ReleaseCandidate,
    actor,
    reason: str,
    correlation_id: str,
) -> ReleaseCandidate:
    blocking_reasons = promotion_blocking_reasons(candidate)
    if blocking_reasons:
        raise ValidationError(
            {
                "code": "promotion_blocked",
                "message": "Release candidate cannot be promoted.",
                "details": {"blocking_reasons": blocking_reasons},
            }
        )

    previous_active_candidate = (
        ReleaseCandidate.objects.select_for_update()
        .filter(
            ai_system=candidate.ai_system,
            status=ReleaseCandidateStatus.ACTIVE,
        )
        .exclude(id=candidate.id)
        .first()
    )

    if previous_active_candidate:
        previous_active_candidate.status = ReleaseCandidateStatus.RETIRED
        previous_active_candidate.save(update_fields=["status", "updated_at"])

    candidate.status = ReleaseCandidateStatus.ACTIVE
    candidate.save(update_fields=["status", "updated_at"])

    PromotionEvent.objects.create(
        ai_system=candidate.ai_system,
        release_candidate=candidate,
        previous_active_candidate=previous_active_candidate,
        promoted_by=actor,
        reason=reason,
    )

    log_audit_event(
        entity_type="ReleaseCandidate",
        entity_id=candidate.id,
        event_type="promoted",
        actor_type=ActorType.USER,
        actor_id=actor.id if actor and actor.is_authenticated else None,
        payload={
            "ai_system_id": candidate.ai_system_id,
            "previous_active_candidate_id": previous_active_candidate.id if previous_active_candidate else None,
            "status": candidate.status,
            "reason": reason,
        },
        correlation_id=correlation_id,
    )

    return candidate


@transaction.atomic
def rollback_release_candidate(
    candidate: ReleaseCandidate,
    actor,
    reason_code: str,
    comment: str,
    correlation_id: str,
):
    blocking_reasons = rollback_blocking_reasons(candidate)
    if blocking_reasons:
        raise ValidationError(
            {
                "code": "rollback_blocked",
                "message": "Release candidate cannot be rolled back.",
                "details": {"blocking_reasons": blocking_reasons},
            }
        )

    target_candidate = rollback_target_for_system(
        candidate.ai_system,
        exclude_candidate_id=candidate.id,
    )

    if target_candidate is None:
        raise ValidationError(
            {
                "code": "rollback_blocked",
                "message": "Rollback target is unavailable.",
                "details": {"blocking_reasons": ["rollback_target_unavailable"]},
            }
        )

    candidate.status = ReleaseCandidateStatus.ROLLED_BACK
    candidate.save(update_fields=["status", "updated_at"])

    target_candidate.status = ReleaseCandidateStatus.ACTIVE
    target_candidate.save(update_fields=["status", "updated_at"])

    rollback_record = RollbackRecord.objects.create(
        ai_system=candidate.ai_system,
        from_candidate=candidate,
        to_candidate=target_candidate,
        reason_code=reason_code,
        comment=comment,
        rolled_back_by=actor,
    )

    log_audit_event(
        entity_type="ReleaseCandidate",
        entity_id=candidate.id,
        event_type="rolled_back",
        actor_type=ActorType.USER,
        actor_id=actor.id if actor and actor.is_authenticated else None,
        payload={
            "ai_system_id": candidate.ai_system_id,
            "to_candidate_id": target_candidate.id,
            "reason_code": reason_code,
            "comment": comment,
            "rollback_record_id": rollback_record.id,
        },
        correlation_id=correlation_id,
    )

    return {
        "from_candidate": candidate,
        "to_candidate": target_candidate,
        "rollback_record": rollback_record,
    }