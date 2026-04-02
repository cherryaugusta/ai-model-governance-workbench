import pytest
from model_bakery import baker

from apps.core.choices import ArtefactStatus, EvalRunStatus, ReleaseCandidateStatus
from apps.evals.services import evaluate_eval_run, queue_candidate_evals
from apps.releases.services import create_release_candidate_snapshot


def build_candidate(*, passing: bool):
    user = baker.make("auth.User")
    system = baker.make(
        "systems.AISystem",
        name="Consumer Support Triage Assistant",
        slug=f"consumer-support-triage-{'pass' if passing else 'fail'}",
        owner_team="Support Operations",
        technical_owner=user,
        business_owner=user,
        risk_tier="high",
        system_type="classification",
        domain_area="consumer_support",
        status="active",
    )

    prompt = baker.make(
        "prompts.PromptVersion",
        ai_system=system,
        name="Strict Triage Prompt" if passing else "Preview Triage Prompt",
        purpose="Classify and route support contacts.",
        version_label="triage-strict-v1" if passing else "triage-preview-v1",
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
        version_label="gpt-4.1-v1" if passing else "gpt-4.1-mini-preview-v1",
        provider_name="openai",
        model_name="gpt-4.1" if passing else "gpt-4.1-mini-preview",
        temperature=0.20,
        max_tokens=512,
        top_p=1.00,
        timeout_ms=2900 if passing else 1400,
        routing_policy={"strategy": "primary"},
        fallback_policy={"enabled": True, "provider_name": "openai", "model_name": "gpt-4.1-mini"} if passing else {},
        cost_budget_per_run=0.0300 if passing else 0.0100,
        status=ArtefactStatus.APPROVED,
        created_by=user,
    )

    candidate = baker.make(
        "releases.ReleaseCandidate",
        ai_system=system,
        prompt_version=prompt,
        model_config=model_config,
        name="RC-1",
        status=ReleaseCandidateStatus.DRAFT,
        eval_dataset_ids=[],
        config_snapshot={},
        created_by=user,
    )
    candidate.config_snapshot = create_release_candidate_snapshot(candidate)
    candidate.status = ReleaseCandidateStatus.PENDING_EVAL
    candidate.save()
    return candidate, user


@pytest.mark.django_db
def test_eval_runner_moves_candidate_to_pending_approval_when_thresholds_pass():
    candidate, user = build_candidate(passing=True)

    queued_runs = queue_candidate_evals(candidate=candidate, actor=user, correlation_id="test-pass")
    assert len(queued_runs) == 3

    for run in queued_runs:
        evaluate_eval_run(run.id, correlation_id="test-pass")

    candidate.refresh_from_db()
    assert candidate.status == ReleaseCandidateStatus.PENDING_APPROVAL
    assert candidate.eval_runs.count() == 3
    assert candidate.eval_runs.filter(status=EvalRunStatus.PASSED).count() == 3

    latest_run = candidate.eval_runs.order_by("-created_at").first()
    assert latest_run is not None
    assert latest_run.summary_metrics["accuracy"] >= 0.82
    assert latest_run.threshold_results["accuracy"]["passed"] is True
    assert latest_run.case_results.count() == 4


@pytest.mark.django_db
def test_eval_runner_moves_candidate_to_eval_failed_when_thresholds_fail():
    candidate, user = build_candidate(passing=False)

    queued_runs = queue_candidate_evals(candidate=candidate, actor=user, correlation_id="test-fail")
    assert len(queued_runs) == 3

    for run in queued_runs:
        evaluate_eval_run(run.id, correlation_id="test-fail")

    candidate.refresh_from_db()
    assert candidate.status == ReleaseCandidateStatus.EVAL_FAILED
    assert candidate.eval_runs.filter(status=EvalRunStatus.FAILED).exists()

    failed_run = candidate.eval_runs.filter(status=EvalRunStatus.FAILED).order_by("-created_at").first()
    assert failed_run is not None
    assert any(item["passed"] is False for item in failed_run.threshold_results.values())
