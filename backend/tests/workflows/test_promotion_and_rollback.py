import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

from apps.core.choices import (
    ApprovalDecision,
    EvalRunStatus,
    ReleaseCandidateStatus,
    RollbackReasonCode,
)
from apps.releases.services import promote_candidate, rollback_release_candidate

User = get_user_model()


@pytest.mark.django_db
def test_promote_candidate_sets_single_active_release():
    user = baker.make(User)
    ai_system = baker.make(
        "systems.AISystem",
        risk_tier="medium",
        status="active",
        technical_owner=user,
        business_owner=user,
    )

    prompt_old = baker.make(
        "prompts.PromptVersion",
        ai_system=ai_system,
        status="approved",
        version_label="v1",
    )
    model_old = baker.make(
        "model_configs.ModelConfig",
        ai_system=ai_system,
        status="approved",
        version_label="v1",
    )
    old_candidate = baker.make(
        "releases.ReleaseCandidate",
        ai_system=ai_system,
        prompt_version=prompt_old,
        model_config=model_old,
        status=ReleaseCandidateStatus.ACTIVE,
        config_snapshot={"submitted_at": "2026-04-01T10:00:00Z"},
        created_by=user,
    )

    prompt_new = baker.make(
        "prompts.PromptVersion",
        ai_system=ai_system,
        status="approved",
        version_label="v2",
    )
    model_new = baker.make(
        "model_configs.ModelConfig",
        ai_system=ai_system,
        status="approved",
        version_label="v2",
    )
    new_candidate = baker.make(
        "releases.ReleaseCandidate",
        ai_system=ai_system,
        prompt_version=prompt_new,
        model_config=model_new,
        status=ReleaseCandidateStatus.APPROVED,
        config_snapshot={"submitted_at": "2026-04-02T10:00:00Z"},
        created_by=user,
    )

    baker.make(
        "evals.EvalRun",
        release_candidate=new_candidate,
        eval_dataset=baker.make("evals.EvalDataset", ai_system=ai_system),
        status=EvalRunStatus.PASSED,
        summary_metrics={"accuracy": 0.9},
        threshold_results={"accuracy": {"passed": True}},
        comparison_to_baseline={},
    )

    baker.make(
        "approvals.ApprovalRecord",
        release_candidate=new_candidate,
        approval_type="technical",
        decision=ApprovalDecision.APPROVED,
        reviewer=user,
    )
    baker.make(
        "approvals.ApprovalRecord",
        release_candidate=new_candidate,
        approval_type="product",
        decision=ApprovalDecision.APPROVED,
        reviewer=user,
    )

    promoted = promote_candidate(
        candidate=new_candidate,
        actor=user,
        reason="Ready for production rollout.",
        correlation_id="test-promotion-1",
    )

    old_candidate.refresh_from_db()
    new_candidate.refresh_from_db()

    assert promoted.id == new_candidate.id
    assert new_candidate.status == ReleaseCandidateStatus.ACTIVE
    assert old_candidate.status == ReleaseCandidateStatus.RETIRED
    assert ai_system.active_release.id == new_candidate.id
    assert ai_system.promotion_events.count() == 1


@pytest.mark.django_db
def test_rollback_candidate_restores_last_approved_release():
    user = baker.make(User)
    ai_system = baker.make(
        "systems.AISystem",
        risk_tier="medium",
        status="active",
        technical_owner=user,
        business_owner=user,
    )

    prompt_previous = baker.make(
        "prompts.PromptVersion",
        ai_system=ai_system,
        status="approved",
        version_label="v1",
    )
    model_previous = baker.make(
        "model_configs.ModelConfig",
        ai_system=ai_system,
        status="approved",
        version_label="v1",
    )
    previous_candidate = baker.make(
        "releases.ReleaseCandidate",
        ai_system=ai_system,
        prompt_version=prompt_previous,
        model_config=model_previous,
        status=ReleaseCandidateStatus.APPROVED,
        config_snapshot={"submitted_at": "2026-04-01T10:00:00Z"},
        created_by=user,
    )

    prompt_current = baker.make(
        "prompts.PromptVersion",
        ai_system=ai_system,
        status="approved",
        version_label="v2",
    )
    model_current = baker.make(
        "model_configs.ModelConfig",
        ai_system=ai_system,
        status="approved",
        version_label="v2",
    )
    current_candidate = baker.make(
        "releases.ReleaseCandidate",
        ai_system=ai_system,
        prompt_version=prompt_current,
        model_config=model_current,
        status=ReleaseCandidateStatus.ACTIVE,
        config_snapshot={"submitted_at": "2026-04-02T10:00:00Z"},
        created_by=user,
    )

    result = rollback_release_candidate(
        candidate=current_candidate,
        actor=user,
        reason_code=RollbackReasonCode.MANUAL_REVERT,
        comment="Restore the previous approved release.",
        correlation_id="test-rollback-1",
    )

    current_candidate.refresh_from_db()
    previous_candidate.refresh_from_db()

    assert current_candidate.status == ReleaseCandidateStatus.ROLLED_BACK
    assert previous_candidate.status == ReleaseCandidateStatus.ACTIVE
    assert result["to_candidate"].id == previous_candidate.id
    assert ai_system.rollback_records.count() == 1
    assert ai_system.active_release.id == previous_candidate.id