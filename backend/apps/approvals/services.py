from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audits.services import log_audit_event
from apps.core.choices import (
    ActorType,
    ApprovalDecision,
    ApprovalType,
    ReleaseCandidateStatus,
)
from apps.releases.models import ReleaseCandidate

from .models import ApprovalRecord


def required_approval_types_for_risk(risk_tier: str) -> list[str]:
    if risk_tier == "low":
        return [ApprovalType.TECHNICAL]

    if risk_tier == "medium":
        return [ApprovalType.TECHNICAL, ApprovalType.PRODUCT]

    if risk_tier == "high":
        return [ApprovalType.TECHNICAL, ApprovalType.PRODUCT, ApprovalType.RISK]

    if risk_tier == "critical":
        return [
            ApprovalType.TECHNICAL,
            ApprovalType.PRODUCT,
            ApprovalType.RISK,
            ApprovalType.GOVERNANCE,
        ]

    raise ValidationError("Unsupported AI system risk tier.")


def approval_summary(candidate: ReleaseCandidate) -> dict:
    required_types = required_approval_types_for_risk(candidate.ai_system.risk_tier)
    records = {
        record.approval_type: record
        for record in candidate.approval_records.all()
    }

    approved_types = []
    pending_types = []
    rejected_types = []
    changes_requested_types = []
    missing_types = []

    for approval_type in required_types:
        record = records.get(approval_type)

        if record is None:
            missing_types.append(approval_type)
            continue

        if record.decision == ApprovalDecision.APPROVED:
            approved_types.append(approval_type)
        elif record.decision == ApprovalDecision.REJECTED:
            rejected_types.append(approval_type)
        elif record.decision == ApprovalDecision.CHANGES_REQUESTED:
            changes_requested_types.append(approval_type)
        else:
            pending_types.append(approval_type)

    return {
        "required_types": required_types,
        "approved_types": approved_types,
        "pending_types": pending_types,
        "rejected_types": rejected_types,
        "changes_requested_types": changes_requested_types,
        "missing_types": missing_types,
        "is_complete": (
            len(approved_types) == len(required_types)
            and not pending_types
            and not rejected_types
            and not changes_requested_types
            and not missing_types
        ),
    }


def all_required_approvals_complete(candidate: ReleaseCandidate) -> bool:
    return approval_summary(candidate)["is_complete"]


def request_candidate_approval(
    candidate: ReleaseCandidate,
    actor,
    correlation_id: str,
) -> list[ApprovalRecord]:
    if candidate.status != ReleaseCandidateStatus.PENDING_APPROVAL:
        raise ValidationError("Only candidates pending approval can initialize approval records.")

    required_types = required_approval_types_for_risk(candidate.ai_system.risk_tier)
    created_or_existing = []

    for approval_type in required_types:
        record, _ = ApprovalRecord.objects.get_or_create(
            release_candidate=candidate,
            approval_type=approval_type,
            defaults={
                "decision": ApprovalDecision.PENDING,
            },
        )
        created_or_existing.append(record)

    log_audit_event(
        entity_type="ReleaseCandidate",
        entity_id=candidate.id,
        event_type="approval_requested",
        actor_type=ActorType.USER,
        actor_id=actor.id if actor and actor.is_authenticated else None,
        payload={
            "status": candidate.status,
            "required_approval_types": required_types,
            "approval_summary": approval_summary(candidate),
        },
        correlation_id=correlation_id,
    )

    return created_or_existing


def record_approval_decision(
    approval: ApprovalRecord,
    actor,
    decision: str,
    comment: str,
    correlation_id: str,
) -> ApprovalRecord:
    if approval.release_candidate.status != ReleaseCandidateStatus.PENDING_APPROVAL:
        raise ValidationError("Approval decisions can only be recorded while the candidate is pending approval.")

    if decision not in {
        ApprovalDecision.APPROVED,
        ApprovalDecision.REJECTED,
        ApprovalDecision.CHANGES_REQUESTED,
    }:
        raise ValidationError("Unsupported approval decision.")

    approval.reviewer = actor
    approval.decision = decision
    approval.comment = comment
    approval.decided_at = timezone.now()
    approval.save()

    candidate = approval.release_candidate

    if decision in {ApprovalDecision.REJECTED, ApprovalDecision.CHANGES_REQUESTED}:
        candidate.status = ReleaseCandidateStatus.REJECTED
        candidate.save(update_fields=["status", "updated_at"])
    elif all_required_approvals_complete(candidate):
        candidate.status = ReleaseCandidateStatus.APPROVED
        candidate.save(update_fields=["status", "updated_at"])

    log_audit_event(
        entity_type="ApprovalRecord",
        entity_id=approval.id,
        event_type="decision_recorded",
        actor_type=ActorType.USER,
        actor_id=actor.id if actor and actor.is_authenticated else None,
        payload={
            "release_candidate_id": candidate.id,
            "approval_type": approval.approval_type,
            "decision": approval.decision,
            "comment": approval.comment,
            "candidate_status": candidate.status,
            "approval_summary": approval_summary(candidate),
        },
        correlation_id=correlation_id,
    )

    return approval
