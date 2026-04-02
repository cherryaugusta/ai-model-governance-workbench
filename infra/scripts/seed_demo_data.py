import os
import sys
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.authtoken.models import Token

from apps.approvals.models import ApprovalRecord
from apps.approvals.services import request_candidate_approval, record_approval_decision
from apps.audits.models import AuditEvent
from apps.core.choices import (
    AISystemStatus,
    ApprovalDecision,
    ArtefactStatus,
    IncidentSeverity,
    IncidentType,
    ReleaseCandidateStatus,
    RiskTier,
    RollbackReasonCode,
)
from apps.evals.models import EvalCase, EvalDataset, EvalRun, EvalRunCaseResult
from apps.evals.services import evaluate_eval_run, queue_candidate_evals
from apps.incidents.models import Incident
from apps.incidents.services import open_incident, resolve_incident
from apps.model_configs.models import ModelConfig
from apps.observability.models import ModelExecutionLog
from apps.prompts.models import PromptVersion
from apps.releases.models import PromotionEvent, ReleaseCandidate, RollbackRecord
from apps.releases.services import promote_candidate, rollback_release_candidate, submit_release_candidate
from apps.systems.models import AISystem

User = get_user_model()


def upsert_user(username: str, email: str, password: str, is_staff: bool = False, is_superuser: bool = False):
    user, _ = User.objects.update_or_create(
        username=username,
        defaults={
            "email": email,
            "is_staff": is_staff,
            "is_superuser": is_superuser,
        },
    )
    user.set_password(password)
    user.save()
    token, _ = Token.objects.get_or_create(user=user)
    return user, token


def reset_domain_data():
    RollbackRecord.objects.all().delete()
    PromotionEvent.objects.all().delete()
    ApprovalRecord.objects.all().delete()
    Incident.objects.all().delete()
    ModelExecutionLog.objects.all().delete()
    EvalRunCaseResult.objects.all().delete()
    EvalRun.objects.all().delete()
    EvalCase.objects.all().delete()
    EvalDataset.objects.all().delete()
    AuditEvent.objects.all().delete()
    ReleaseCandidate.objects.all().delete()
    PromptVersion.objects.all().delete()
    ModelConfig.objects.all().delete()
    AISystem.objects.all().delete()


def create_system(
    *,
    name: str,
    slug: str,
    description: str,
    owner_team: str,
    technical_owner,
    business_owner,
    risk_tier: str,
    system_type: str,
    domain_area: str,
):
    return AISystem.objects.create(
        name=name,
        slug=slug,
        description=description,
        owner_team=owner_team,
        technical_owner=technical_owner,
        business_owner=business_owner,
        risk_tier=risk_tier,
        system_type=system_type,
        domain_area=domain_area,
        status=AISystemStatus.ACTIVE,
    )


def create_prompt(
    *,
    ai_system,
    name: str,
    purpose: str,
    version_label: str,
    status: str,
    template_text: str,
    created_by,
):
    return PromptVersion.objects.create(
        ai_system=ai_system,
        name=name,
        purpose=purpose,
        version_label=version_label,
        status=status,
        template_text=template_text,
        schema_version="1.0",
        input_contract={
            "type": "object",
            "required": ["text"],
        },
        output_contract={
            "type": "object",
            "required": ["label", "requires_review"],
        },
        created_by=created_by,
    )


def create_model_config(
    *,
    ai_system,
    version_label: str,
    provider_name: str,
    model_name: str,
    temperature: str,
    max_tokens: int,
    top_p: str,
    timeout_ms: int,
    routing_policy: dict,
    fallback_policy: dict,
    cost_budget_per_run: str,
    status: str,
    created_by,
):
    return ModelConfig.objects.create(
        ai_system=ai_system,
        version_label=version_label,
        provider_name=provider_name,
        model_name=model_name,
        temperature=Decimal(temperature),
        max_tokens=max_tokens,
        top_p=Decimal(top_p),
        timeout_ms=timeout_ms,
        routing_policy=routing_policy,
        fallback_policy=fallback_policy,
        cost_budget_per_run=Decimal(cost_budget_per_run),
        status=status,
        created_by=created_by,
    )


def create_candidate(
    *,
    ai_system,
    prompt_version,
    model_config,
    name: str,
    created_by,
):
    return ReleaseCandidate.objects.create(
        ai_system=ai_system,
        prompt_version=prompt_version,
        model_config=model_config,
        name=name,
        created_by=created_by,
    )


def ensure_status(candidate, expected_status: str, step_name: str):
    candidate.refresh_from_db()
    if candidate.status != expected_status:
        raise RuntimeError(
            f"{step_name} expected candidate '{candidate.name}' to be '{expected_status}' but found '{candidate.status}'."
        )


def submit_and_run_evals(candidate, actor):
    submit_release_candidate(
        candidate=candidate,
        actor=actor,
        correlation_id=f"seed-submit-{candidate.id}",
    )
    ensure_status(candidate, ReleaseCandidateStatus.PENDING_EVAL, "submit_release_candidate")

    queued_runs = queue_candidate_evals(
        candidate=candidate,
        actor=actor,
        correlation_id=f"seed-evals-{candidate.id}",
    )

    for run in queued_runs:
        evaluate_eval_run(
            eval_run_id=run.id,
            correlation_id=f"seed-evals-{candidate.id}",
        )

    candidate.refresh_from_db()
    return queued_runs


def request_approvals_for_candidate(candidate, actor):
    ensure_status(candidate, ReleaseCandidateStatus.PENDING_APPROVAL, "request_candidate_approval precondition")
    request_candidate_approval(
        candidate=candidate,
        actor=actor,
        correlation_id=f"seed-approval-request-{candidate.id}",
    )
    candidate.refresh_from_db()


def approve_all(candidate, actor):
    records = list(candidate.approval_records.order_by("approval_type"))
    if not records:
        raise RuntimeError(f"approve_all found no approval records for candidate '{candidate.name}'.")

    for record in records:
        record_approval_decision(
            approval=record,
            actor=actor,
            decision=ApprovalDecision.APPROVED,
            comment=f"Seed approval recorded for {record.approval_type}.",
            correlation_id=f"seed-approval-decision-{candidate.id}-{record.approval_type}",
        )

    ensure_status(candidate, ReleaseCandidateStatus.APPROVED, "approve_all completion")


def promote(candidate, actor, reason: str):
    ensure_status(candidate, ReleaseCandidateStatus.APPROVED, "promote precondition")
    promote_candidate(
        candidate=candidate,
        actor=actor,
        reason=reason,
        correlation_id=f"seed-promote-{candidate.id}",
    )
    ensure_status(candidate, ReleaseCandidateStatus.ACTIVE, "promote completion")


def summarize():
    return {
        "systems": AISystem.objects.count(),
        "prompt_versions": PromptVersion.objects.count(),
        "model_configs": ModelConfig.objects.count(),
        "release_candidates": ReleaseCandidate.objects.count(),
        "eval_datasets": EvalDataset.objects.count(),
        "eval_cases": EvalCase.objects.count(),
        "eval_runs": EvalRun.objects.count(),
        "approval_records": ApprovalRecord.objects.count(),
        "incidents": Incident.objects.count(),
        "promotion_events": PromotionEvent.objects.count(),
        "rollback_records": RollbackRecord.objects.count(),
        "audit_events": AuditEvent.objects.count(),
        "active_releases": ReleaseCandidate.objects.filter(status=ReleaseCandidateStatus.ACTIVE).count(),
        "pending_approval_candidates": ReleaseCandidate.objects.filter(status=ReleaseCandidateStatus.PENDING_APPROVAL).count(),
        "eval_failed_candidates": ReleaseCandidate.objects.filter(status=ReleaseCandidateStatus.EVAL_FAILED).count(),
        "draft_candidates": ReleaseCandidate.objects.filter(status=ReleaseCandidateStatus.DRAFT).count(),
        "approved_candidates": ReleaseCandidate.objects.filter(status=ReleaseCandidateStatus.APPROVED).count(),
        "rolled_back_candidates": ReleaseCandidate.objects.filter(status=ReleaseCandidateStatus.ROLLED_BACK).count(),
    }


@transaction.atomic
def main():
    admin_user, admin_token = upsert_user(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        is_staff=True,
        is_superuser=True,
    )
    operator_user, operator_token = upsert_user(
        username="operator",
        email="operator@example.com",
        password="operatorpass123",
    )
    technical_user, technical_token = upsert_user(
        username="tech_reviewer",
        email="tech@example.com",
        password="reviewpass123",
    )
    product_user, product_token = upsert_user(
        username="product_reviewer",
        email="product@example.com",
        password="reviewpass123",
    )
    risk_user, risk_token = upsert_user(
        username="risk_reviewer",
        email="risk@example.com",
        password="reviewpass123",
    )
    governance_user, governance_token = upsert_user(
        username="governance_reviewer",
        email="governance@example.com",
        password="reviewpass123",
    )

    reset_domain_data()

    system_1 = create_system(
        name="Consumer Support Triage Assistant",
        slug="consumer-support-triage-assistant",
        description="Routes support complaints into governed triage categories and review queues.",
        owner_team="Consumer Operations AI",
        technical_owner=technical_user,
        business_owner=product_user,
        risk_tier=RiskTier.HIGH,
        system_type="classification",
        domain_area="customer-support",
    )
    system_2 = create_system(
        name="Policy Summary Assistant",
        slug="policy-summary-assistant",
        description="Summarizes policy documents for internal support operations.",
        owner_team="Policy Enablement",
        technical_owner=technical_user,
        business_owner=product_user,
        risk_tier=RiskTier.MEDIUM,
        system_type="summarization",
        domain_area="policy-ops",
    )
    system_3 = create_system(
        name="Support Note Classifier",
        slug="support-note-classifier",
        description="Classifies support notes into escalation and quality categories.",
        owner_team="Support Excellence",
        technical_owner=technical_user,
        business_owner=operator_user,
        risk_tier=RiskTier.LOW,
        system_type="classification",
        domain_area="support-ops",
    )
    system_4 = create_system(
        name="Evidence Extractor",
        slug="evidence-extractor",
        description="Extracts structured evidence fields from regulated operational records.",
        owner_team="Risk Controls",
        technical_owner=technical_user,
        business_owner=risk_user,
        risk_tier=RiskTier.CRITICAL,
        system_type="structured-extraction",
        domain_area="risk-ops",
    )

    s1_prompt_v1 = create_prompt(
        ai_system=system_1,
        name="Strict Triage Prompt",
        purpose="Stable governed complaint triage baseline.",
        version_label="triage-strict-v1",
        status=ArtefactStatus.APPROVED,
        template_text="Strictly classify the complaint, preserve schema validity, and indicate whether human review is required.",
        created_by=admin_user,
    )
    s1_prompt_v2 = create_prompt(
        ai_system=system_1,
        name="Triage Preview Prompt",
        purpose="Experimental escalation-sensitive triage prompt.",
        version_label="triage-preview-v2",
        status=ArtefactStatus.CANDIDATE,
        template_text="Classify the complaint, prioritize escalations, and optimize for low cost under preview constraints.",
        created_by=admin_user,
    )
    s2_prompt_v1 = create_prompt(
        ai_system=system_2,
        name="Strict Policy Summary Prompt",
        purpose="Stable policy summarization baseline.",
        version_label="policy-strict-v1",
        status=ArtefactStatus.APPROVED,
        template_text="Strictly summarize the policy and preserve mandatory control language.",
        created_by=admin_user,
    )
    s2_prompt_v2 = create_prompt(
        ai_system=system_2,
        name="Context-Aware Policy Summary Prompt",
        purpose="Improved structure for policy support workflows.",
        version_label="policy-context-v2",
        status=ArtefactStatus.CANDIDATE,
        template_text="Summarize the policy, call out mandatory controls, and surface escalation conditions.",
        created_by=admin_user,
    )
    s3_prompt_v1 = create_prompt(
        ai_system=system_3,
        name="Strict Support Note Prompt",
        purpose="Stable support note classification baseline.",
        version_label="support-strict-v1",
        status=ArtefactStatus.APPROVED,
        template_text="Strictly classify the support note and preserve consistent routing labels.",
        created_by=admin_user,
    )
    s3_prompt_v2 = create_prompt(
        ai_system=system_3,
        name="Review-Sensitive Support Note Prompt",
        purpose="Adds review emphasis for ambiguous notes.",
        version_label="support-review-v2",
        status=ArtefactStatus.CANDIDATE,
        template_text="Classify the support note, flag ambiguous notes, and indicate whether review is required.",
        created_by=admin_user,
    )
    s4_prompt_v1 = create_prompt(
        ai_system=system_4,
        name="Strict Evidence Extraction Prompt",
        purpose="Stable regulated evidence extraction baseline.",
        version_label="evidence-strict-v1",
        status=ArtefactStatus.APPROVED,
        template_text="Strictly extract the required evidence fields and return a schema-valid object.",
        created_by=admin_user,
    )
    s4_prompt_v2 = create_prompt(
        ai_system=system_4,
        name="Extended Evidence Extraction Prompt",
        purpose="Higher-control extraction for review workflows.",
        version_label="evidence-extended-v2",
        status=ArtefactStatus.CANDIDATE,
        template_text="Extract the required evidence fields, preserve schema validity, and surface review conditions.",
        created_by=admin_user,
    )

    s1_config_v1 = create_model_config(
        ai_system=system_1,
        version_label="gpt-4.1-v1",
        provider_name="openai",
        model_name="gpt-4.1",
        temperature="0.10",
        max_tokens=640,
        top_p="1.00",
        timeout_ms=2900,
        routing_policy={"mode": "primary_only"},
        fallback_policy={"enabled": False},
        cost_budget_per_run="0.0300",
        status=ArtefactStatus.APPROVED,
        created_by=admin_user,
    )
    s1_config_v2 = create_model_config(
        ai_system=system_1,
        version_label="gpt-4.1-mini-preview-v2",
        provider_name="openai",
        model_name="gpt-4.1-mini-preview",
        temperature="0.20",
        max_tokens=384,
        top_p="1.00",
        timeout_ms=1500,
        routing_policy={"mode": "primary_only"},
        fallback_policy={"enabled": False},
        cost_budget_per_run="0.0120",
        status=ArtefactStatus.CANDIDATE,
        created_by=admin_user,
    )
    s2_config_v1 = create_model_config(
        ai_system=system_2,
        version_label="gpt-4.1-v1",
        provider_name="openai",
        model_name="gpt-4.1",
        temperature="0.10",
        max_tokens=640,
        top_p="1.00",
        timeout_ms=2900,
        routing_policy={"mode": "primary_only"},
        fallback_policy={"enabled": False},
        cost_budget_per_run="0.0300",
        status=ArtefactStatus.APPROVED,
        created_by=admin_user,
    )
    s2_config_v2 = create_model_config(
        ai_system=system_2,
        version_label="gpt-4.1-v2",
        provider_name="openai",
        model_name="gpt-4.1",
        temperature="0.12",
        max_tokens=640,
        top_p="1.00",
        timeout_ms=2850,
        routing_policy={"mode": "primary_only"},
        fallback_policy={"enabled": False},
        cost_budget_per_run="0.0220",
        status=ArtefactStatus.CANDIDATE,
        created_by=admin_user,
    )
    s3_config_v1 = create_model_config(
        ai_system=system_3,
        version_label="gpt-4.1-v1",
        provider_name="openai",
        model_name="gpt-4.1",
        temperature="0.10",
        max_tokens=640,
        top_p="1.00",
        timeout_ms=2900,
        routing_policy={"mode": "primary_only"},
        fallback_policy={"enabled": False},
        cost_budget_per_run="0.0300",
        status=ArtefactStatus.APPROVED,
        created_by=admin_user,
    )
    s3_config_v2 = create_model_config(
        ai_system=system_3,
        version_label="gpt-4.1-fast-v2",
        provider_name="openai",
        model_name="gpt-4.1-fast",
        temperature="0.10",
        max_tokens=512,
        top_p="1.00",
        timeout_ms=2600,
        routing_policy={"mode": "primary_only"},
        fallback_policy={"enabled": False},
        cost_budget_per_run="0.0190",
        status=ArtefactStatus.CANDIDATE,
        created_by=admin_user,
    )
    s4_config_v1 = create_model_config(
        ai_system=system_4,
        version_label="gpt-4.1-v1",
        provider_name="openai",
        model_name="gpt-4.1",
        temperature="0.10",
        max_tokens=640,
        top_p="1.00",
        timeout_ms=2900,
        routing_policy={"mode": "primary_only"},
        fallback_policy={"enabled": False},
        cost_budget_per_run="0.0300",
        status=ArtefactStatus.APPROVED,
        created_by=admin_user,
    )
    s4_config_v2 = create_model_config(
        ai_system=system_4,
        version_label="gpt-4.1-v2",
        provider_name="openai",
        model_name="gpt-4.1",
        temperature="0.10",
        max_tokens=768,
        top_p="1.00",
        timeout_ms=2900,
        routing_policy={"mode": "primary_only"},
        fallback_policy={"enabled": False},
        cost_budget_per_run="0.0220",
        status=ArtefactStatus.CANDIDATE,
        created_by=admin_user,
    )

    rc1 = create_candidate(
        ai_system=system_1,
        prompt_version=s1_prompt_v1,
        model_config=s1_config_v1,
        name="Current approved triage baseline",
        created_by=admin_user,
    )
    submit_and_run_evals(rc1, admin_user)
    request_approvals_for_candidate(rc1, admin_user)
    approve_all(rc1, admin_user)
    promote(rc1, admin_user, "Seed baseline promotion for consumer support triage.")

    rc2 = create_candidate(
        ai_system=system_1,
        prompt_version=s1_prompt_v2,
        model_config=s1_config_v2,
        name="Blocked low-cost preview triage candidate",
        created_by=admin_user,
    )
    submit_and_run_evals(rc2, admin_user)
    ensure_status(rc2, ReleaseCandidateStatus.EVAL_FAILED, "blocked candidate eval outcome")

    rc3 = create_candidate(
        ai_system=system_2,
        prompt_version=s2_prompt_v1,
        model_config=s2_config_v1,
        name="Current approved policy summary baseline",
        created_by=admin_user,
    )
    submit_and_run_evals(rc3, admin_user)
    request_approvals_for_candidate(rc3, admin_user)
    approve_all(rc3, admin_user)
    promote(rc3, admin_user, "Seed baseline promotion for policy summary.")

    rc4 = create_candidate(
        ai_system=system_2,
        prompt_version=s2_prompt_v2,
        model_config=s2_config_v2,
        name="Context-aware policy summary draft",
        created_by=admin_user,
    )

    rc5 = create_candidate(
        ai_system=system_3,
        prompt_version=s3_prompt_v1,
        model_config=s3_config_v1,
        name="Current approved support note baseline",
        created_by=admin_user,
    )
    submit_and_run_evals(rc5, admin_user)
    request_approvals_for_candidate(rc5, admin_user)
    approve_all(rc5, admin_user)
    promote(rc5, admin_user, "Seed baseline promotion for support note classifier.")

    rc6 = create_candidate(
        ai_system=system_3,
        prompt_version=s3_prompt_v2,
        model_config=s3_config_v2,
        name="Review-sensitive support note draft",
        created_by=admin_user,
    )

    rc7 = create_candidate(
        ai_system=system_4,
        prompt_version=s4_prompt_v1,
        model_config=s4_config_v1,
        name="Approved evidence extraction rollback target",
        created_by=admin_user,
    )
    submit_and_run_evals(rc7, admin_user)
    request_approvals_for_candidate(rc7, admin_user)
    approve_all(rc7, admin_user)
    ensure_status(rc7, ReleaseCandidateStatus.APPROVED, "rollback target approval state")

    rc8 = create_candidate(
        ai_system=system_4,
        prompt_version=s4_prompt_v2,
        model_config=s4_config_v1,
        name="Active evidence extraction release",
        created_by=admin_user,
    )
    submit_and_run_evals(rc8, admin_user)
    request_approvals_for_candidate(rc8, admin_user)
    approve_all(rc8, admin_user)
    promote(rc8, admin_user, "Promoted newer evidence extraction release for rollback demo.")

    incident_1 = open_incident(
        ai_system=system_4,
        release_candidate=rc8,
        incident_type=IncidentType.LATENCY_BREACH,
        severity=IncidentSeverity.HIGH,
        summary="Latency spike detected on active evidence extraction release",
        description="A controlled demo incident links an operational problem to the active release before rollback.",
        actor=admin_user,
        correlation_id="seed-incident-system-4-high",
    )

    rollback_release_candidate(
        candidate=rc8,
        actor=admin_user,
        reason_code=RollbackReasonCode.INCIDENT_RESPONSE,
        comment="Rollback executed during demo seeding after latency breach.",
        correlation_id="seed-rollback-system-4",
    )

    resolve_incident(
        incident=incident_1,
        actor=admin_user,
        resolution_notes="Rollback restored the previous approved evidence extraction baseline.",
        correlation_id="seed-resolve-incident-system-4-high",
    )

    rc7.refresh_from_db()
    rc8.refresh_from_db()

    incident_2 = open_incident(
        ai_system=system_2,
        release_candidate=rc3,
        incident_type=IncidentType.MANUAL_REPORT,
        severity=IncidentSeverity.LOW,
        summary="Manual review report for policy summary wording",
        description="Low-severity report opened to make the incident dashboard non-empty without blocking promotion.",
        actor=operator_user,
        correlation_id="seed-incident-system-2-low",
    )

    incident_3 = open_incident(
        ai_system=system_4,
        release_candidate=rc7,
        incident_type=IncidentType.SCHEMA_FAILURE,
        severity=IncidentSeverity.CRITICAL,
        summary="Critical schema failure reported on active evidence extraction baseline",
        description="This open critical incident is left unresolved to demonstrate promotion blocking on operational severity.",
        actor=risk_user,
        correlation_id="seed-incident-system-4-critical",
    )

    rc9 = create_candidate(
        ai_system=system_4,
        prompt_version=s4_prompt_v2,
        model_config=s4_config_v1,
        name="Strict evidence extraction review candidate",
        created_by=admin_user,
    )
    submit_and_run_evals(rc9, admin_user)
    request_approvals_for_candidate(rc9, admin_user)
    ensure_status(rc9, ReleaseCandidateStatus.PENDING_APPROVAL, "post-approval-request pending queue state")

    summary = summarize()

    print("Seed complete.")
    print(f"Admin token: {admin_token.key}")
    print(f"Operator token: {operator_token.key}")
    print(f"Technical reviewer token: {technical_token.key}")
    print(f"Product reviewer token: {product_token.key}")
    print(f"Risk reviewer token: {risk_token.key}")
    print(f"Governance reviewer token: {governance_token.key}")
    print(f"System 1 active release: {system_1.active_release.name if system_1.active_release else 'none'}")
    print(f"System 2 active release: {system_2.active_release.name if system_2.active_release else 'none'}")
    print(f"System 3 active release: {system_3.active_release.name if system_3.active_release else 'none'}")
    print(f"System 4 active release: {system_4.active_release.name if system_4.active_release else 'none'}")
    print(summary)
    print(f"Resolved incident id: {incident_1.id}")
    print(f"Open incident id: {incident_2.id}")
    print(f"Blocking incident id: {incident_3.id}")
    print(f"Rollback records: {RollbackRecord.objects.count()}")


if __name__ == "__main__":
    main()
