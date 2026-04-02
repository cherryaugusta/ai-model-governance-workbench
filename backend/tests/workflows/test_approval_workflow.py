import pytest
from model_bakery import baker

from apps.approvals.services import request_candidate_approval, record_approval_decision
from apps.core.choices import (
    ApprovalDecision,
    ApprovalType,
    ArtefactStatus,
    ReleaseCandidateStatus,
)
from apps.releases.services import create_release_candidate_snapshot


def build_candidate(*, risk_tier="high"):
    user = baker.make("auth.User")
    system = baker.make(
        "systems.AISystem",
        name="Consumer Support Triage Assistant",
        slug=f"consumer-support-triage-{risk_tier}",
        owner_team="Support Operations",
        technical_owner=user,
        business_owner=user,
        risk_tier=risk_tier,
        system_type="classification",
        domain_area="consumer_support",
        status="active",
    )

    prompt = baker.make(
        "prompts.PromptVersion",
        ai_system=system,
        name="Strict Triage Prompt",
        purpose="Classify and route support contacts.",
        version_label=f"triage-{risk_tier}-v1",
        status=ArtefactStatus.APPROVED,
        template_text="Return a structured triage decision.",
        schema_version="1.0",
        input_contract={"text": "string"},
        output_contract={"label": "string", "requires_review": "boolean"},
        created_by=user,
    )

    model_config = baker.make(
        "model_configs.ModelConfig",
        ai_system=system,
        version_label=f"gpt-4.1-{risk_tier}-v1",
        provider_name="openai",
        model_name="gpt-4.1",
        temperature=0.20,
        max_tokens=512,
        top_p=1.00,
        timeout_ms=2900,
        routing_policy={"strategy": "primary"},
        fallback_policy={"enabled": True, "provider_name": "openai", "model_name": "gpt-4.1-mini"},
        cost_budget_per_run=0.0300,
        status=ArtefactStatus.APPROVED,
        created_by=user,
    )

    candidate = baker.prepare(
        "releases.ReleaseCandidate",
        ai_system=system,
        prompt_version=prompt,
        model_config=model_config,
        name="RC-approval",
        status=ReleaseCandidateStatus.PENDING_APPROVAL,
        eval_dataset_ids=[],
        config_snapshot={},
        created_by=user,
    )
    candidate.config_snapshot = create_release_candidate_snapshot(candidate)
    candidate.save()
    return candidate, user


@pytest.mark.django_db
def test_request_candidate_approval_creates_required_records_for_high_risk():
    candidate, user = build_candidate(risk_tier="high")

    approvals = request_candidate_approval(
        candidate=candidate,
        actor=user,
        correlation_id="approval-request",
    )

    assert len(approvals) == 3
    assert candidate.approval_records.count() == 3
    assert set(candidate.approval_records.values_list("approval_type", flat=True)) == {
        ApprovalType.TECHNICAL,
        ApprovalType.PRODUCT,
        ApprovalType.RISK,
    }
    assert set(candidate.approval_records.values_list("decision", flat=True)) == {
        ApprovalDecision.PENDING,
    }


@pytest.mark.django_db
def test_approving_all_required_records_moves_candidate_to_approved():
    candidate, user = build_candidate(risk_tier="high")

    request_candidate_approval(
        candidate=candidate,
        actor=user,
        correlation_id="approval-request",
    )

    for approval in candidate.approval_records.order_by("approval_type"):
        record_approval_decision(
            approval=approval,
            actor=user,
            decision=ApprovalDecision.APPROVED,
            comment=f"approved-{approval.approval_type}",
            correlation_id="approval-approve",
        )

    candidate.refresh_from_db()
    assert candidate.status == ReleaseCandidateStatus.APPROVED
    assert candidate.approval_records.filter(decision=ApprovalDecision.APPROVED).count() == 3


@pytest.mark.django_db
def test_rejecting_one_required_record_moves_candidate_to_rejected():
    candidate, user = build_candidate(risk_tier="medium")

    request_candidate_approval(
        candidate=candidate,
        actor=user,
        correlation_id="approval-request",
    )

    technical = candidate.approval_records.get(approval_type=ApprovalType.TECHNICAL)

    record_approval_decision(
        approval=technical,
        actor=user,
        decision=ApprovalDecision.REJECTED,
        comment="rejected-technical",
        correlation_id="approval-reject",
    )

    candidate.refresh_from_db()
    technical.refresh_from_db()

    assert technical.decision == ApprovalDecision.REJECTED
    assert candidate.status == ReleaseCandidateStatus.REJECTED
