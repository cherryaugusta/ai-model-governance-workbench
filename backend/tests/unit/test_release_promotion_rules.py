import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

from apps.core.choices import ReleaseCandidateStatus
from apps.releases.services import (
    promotion_blocking_reasons,
    rollback_blocking_reasons,
)

User = get_user_model()


@pytest.mark.django_db
def test_promotion_blocked_when_candidate_not_approved():
    user = baker.make(User)
    ai_system = baker.make(
        "systems.AISystem",
        risk_tier="high",
        status="active",
        technical_owner=user,
        business_owner=user,
    )
    prompt = baker.make(
        "prompts.PromptVersion",
        ai_system=ai_system,
        status="approved",
    )
    model_config = baker.make(
        "model_configs.ModelConfig",
        ai_system=ai_system,
        status="approved",
    )
    candidate = baker.make(
        "releases.ReleaseCandidate",
        ai_system=ai_system,
        prompt_version=prompt,
        model_config=model_config,
        status=ReleaseCandidateStatus.PENDING_APPROVAL,
        config_snapshot={"submitted_at": "2026-04-02T12:00:00Z"},
        created_by=user,
    )

    reasons = promotion_blocking_reasons(candidate)

    assert "candidate_not_approved" in reasons
    assert "latest_eval_missing" in reasons
    assert "required_approvals_incomplete" in reasons


@pytest.mark.django_db
def test_rollback_blocked_when_candidate_not_active():
    user = baker.make(User)
    ai_system = baker.make(
        "systems.AISystem",
        status="active",
        technical_owner=user,
        business_owner=user,
    )
    prompt = baker.make(
        "prompts.PromptVersion",
        ai_system=ai_system,
        status="approved",
    )
    model_config = baker.make(
        "model_configs.ModelConfig",
        ai_system=ai_system,
        status="approved",
    )
    candidate = baker.make(
        "releases.ReleaseCandidate",
        ai_system=ai_system,
        prompt_version=prompt,
        model_config=model_config,
        status=ReleaseCandidateStatus.APPROVED,
        config_snapshot={"submitted_at": "2026-04-02T12:00:00Z"},
        created_by=user,
    )

    reasons = rollback_blocking_reasons(candidate)

    assert "candidate_not_active" in reasons