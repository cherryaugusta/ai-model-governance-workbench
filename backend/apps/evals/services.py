from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from statistics import mean

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audits.services import log_audit_event
from apps.core.choices import (
    ActorType,
    EvalRunStatus,
    ExecutionStatus,
    ReleaseCandidateStatus,
)
from apps.releases.models import ReleaseCandidate

from .models import EvalCase, EvalDataset, EvalRun, EvalRunCaseResult


DEFAULT_THRESHOLD_PROFILE = {
    "accuracy_min": 0.82,
    "schema_valid_rate_min": 0.98,
    "p95_latency_ms_max": 2500,
    "mean_cost_estimate_max": 0.02,
    "timeout_rate_max": 0.02,
}

DATASET_DIRECTORIES = {
    "baseline": "baseline_cases",
    "regression": "regression_cases",
    "adversarial": "adversarial_cases",
}


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def stable_ratio(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(16**12 - 1)


def percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil((pct / 100) * len(ordered)) - 1)
    return float(ordered[index])


def filesystem_dataset_root() -> Path:
    return Path(settings.BASE_DIR) / "evals" / "datasets"


def sync_eval_datasets_for_system(ai_system) -> list[EvalDataset]:
    dataset_root = filesystem_dataset_root()
    created_or_updated = []

    for scenario_type, folder_name in DATASET_DIRECTORIES.items():
        folder_path = dataset_root / folder_name
        if not folder_path.exists():
            continue

        dataset, _ = EvalDataset.objects.get_or_create(
            ai_system=ai_system,
            slug=scenario_type,
            defaults={
                "name": f"{scenario_type.title()} Cases",
                "description": f"Filesystem-backed {scenario_type} evaluation suite.",
                "scenario_type": scenario_type,
                "threshold_profile": DEFAULT_THRESHOLD_PROFILE,
                "is_active": True,
            },
        )

        dataset.name = f"{scenario_type.title()} Cases"
        dataset.description = f"Filesystem-backed {scenario_type} evaluation suite."
        dataset.scenario_type = scenario_type
        dataset.threshold_profile = DEFAULT_THRESHOLD_PROFILE
        dataset.is_active = True
        dataset.save()

        for json_file in sorted(folder_path.glob("*.json")):
            payload = json.loads(json_file.read_text(encoding="utf-8"))
            EvalCase.objects.update_or_create(
                eval_dataset=dataset,
                case_id=payload["case_id"],
                defaults={
                    "scenario_type": payload.get("scenario_type", scenario_type),
                    "input_payload": payload.get("input_payload", {}),
                    "ground_truth": payload.get("ground_truth", {}),
                    "expected_metrics": payload.get("expected_metrics", {}),
                    "tags": payload.get("tags", []),
                },
            )

        created_or_updated.append(dataset)

    return created_or_updated


def selected_eval_datasets(candidate: ReleaseCandidate) -> list[EvalDataset]:
    sync_eval_datasets_for_system(candidate.ai_system)

    queryset = EvalDataset.objects.filter(
        ai_system=candidate.ai_system,
        is_active=True,
    ).order_by("name")

    if candidate.eval_dataset_ids:
        queryset = queryset.filter(id__in=candidate.eval_dataset_ids)

    datasets = list(queryset)

    if not datasets:
        raise ValidationError("No active eval datasets are available for this release candidate.")

    return datasets


def candidate_profile(candidate: ReleaseCandidate) -> dict:
    snapshot = candidate.config_snapshot or {}
    prompt_snapshot = snapshot.get("prompt_version", {})
    model_snapshot = snapshot.get("model_config", {})

    prompt_name = str(prompt_snapshot.get("name", "")).lower()
    prompt_version_label = str(prompt_snapshot.get("version_label", "")).lower()
    model_name = str(model_snapshot.get("model_name", "")).lower()
    model_version_label = str(model_snapshot.get("version_label", "")).lower()
    timeout_ms = int(model_snapshot.get("timeout_ms", 2500))
    cost_budget = float(model_snapshot.get("cost_budget_per_run", 0.02))
    fallback_policy = model_snapshot.get("fallback_policy", {}) or {}
    fallback_enabled = bool(fallback_policy)

    accuracy = 0.93
    schema_valid_rate = 0.995
    timeout_rate = 0.008
    mean_latency_ms = 1600.0
    mean_cost_estimate = 0.0165
    fallback_success_rate = 0.78

    if "mini" in model_name or "small" in model_name or "mini" in model_version_label:
        accuracy -= 0.11
        mean_latency_ms -= 180
        mean_cost_estimate -= 0.0045

    if "preview" in model_name or "experimental" in model_name or "preview" in model_version_label:
        accuracy -= 0.05
        schema_valid_rate -= 0.03
        timeout_rate += 0.012

    if "fast" in model_name or "turbo" in model_name:
        accuracy -= 0.02
        mean_latency_ms -= 140

    if "strict" in prompt_name or "strict" in prompt_version_label:
        accuracy += 0.02
        schema_valid_rate += 0.004

    if "triage" in prompt_name or "triage" in prompt_version_label:
        accuracy += 0.01

    if timeout_ms < 1800:
        timeout_rate += 0.03
        accuracy -= 0.03
    elif timeout_ms < 2200:
        timeout_rate += 0.015
        accuracy -= 0.01
    elif timeout_ms >= 2800:
        timeout_rate -= 0.003

    if cost_budget < 0.015:
        accuracy -= 0.035
        schema_valid_rate -= 0.012
    elif cost_budget > 0.025:
        accuracy += 0.008
        mean_cost_estimate += 0.0006

    if fallback_enabled:
        fallback_success_rate += 0.16
        timeout_rate -= 0.004
        mean_cost_estimate += 0.0005
        accuracy += 0.004

    return {
        "accuracy": clamp(accuracy, 0.45, 0.995),
        "schema_valid_rate": clamp(schema_valid_rate, 0.70, 0.999),
        "timeout_rate": clamp(timeout_rate, 0.0, 0.40),
        "mean_latency_ms": max(mean_latency_ms, 200.0),
        "mean_cost_estimate": clamp(mean_cost_estimate, 0.001, 0.05),
        "fallback_success_rate": clamp(fallback_success_rate, 0.0, 1.0),
        "fallback_enabled": fallback_enabled,
    }


def scenario_modifiers(eval_case: EvalCase) -> dict:
    scenario = (eval_case.scenario_type or eval_case.eval_dataset.scenario_type).lower()

    if scenario == "baseline":
        return {
            "accuracy": 0.0,
            "schema": 0.0,
            "timeout": 0.0,
            "latency_shift": 0.0,
            "cost_shift": 0.0,
            "fallback": 0.0,
        }

    if scenario == "regression":
        return {
            "accuracy": -0.015,
            "schema": -0.002,
            "timeout": 0.003,
            "latency_shift": 110.0,
            "cost_shift": 0.0006,
            "fallback": -0.02,
        }

    if scenario == "adversarial":
        return {
            "accuracy": -0.03,
            "schema": -0.006,
            "timeout": 0.006,
            "latency_shift": 220.0,
            "cost_shift": 0.0012,
            "fallback": -0.04,
        }

    return {
        "accuracy": -0.01,
        "schema": 0.0,
        "timeout": 0.0,
        "latency_shift": 0.0,
        "cost_shift": 0.0,
        "fallback": 0.0,
    }


def case_difficulty(eval_case: EvalCase) -> float:
    scenario = (eval_case.scenario_type or eval_case.eval_dataset.scenario_type).lower()
    tags = set(eval_case.tags or [])

    difficulty = 0.78

    if scenario == "baseline":
        difficulty += 0.00
    elif scenario == "regression":
        difficulty += 0.05
    elif scenario == "adversarial":
        difficulty += 0.09
    else:
        difficulty += 0.03

    if "fraud" in tags:
        difficulty += 0.015
    if "manual_review" in tags:
        difficulty += 0.015
    if "instruction_override" in tags:
        difficulty += 0.02
    if "malformed_input" in tags:
        difficulty += 0.025
    if "ambiguous" in tags:
        difficulty += 0.02
    if "sarcasm" in tags:
        difficulty += 0.015
    if "urgent" in tags:
        difficulty += 0.01

    return clamp(difficulty, 0.70, 0.95)


def alternate_label(expected_label: str) -> str:
    labels = [
        "billing_dispute",
        "fraud_report",
        "account_access",
        "consumer_understanding",
        "refund_request",
        "manual_review",
        "policy_clarification",
    ]
    if expected_label not in labels:
        return labels[0]
    current_index = labels.index(expected_label)
    return labels[(current_index + 1) % len(labels)]


def stable_case_seed(candidate: ReleaseCandidate, eval_case: EvalCase) -> str:
    snapshot = candidate.config_snapshot or {}
    ai_system_snapshot = snapshot.get("ai_system", {})
    prompt_snapshot = snapshot.get("prompt_version", {})
    model_snapshot = snapshot.get("model_config", {})

    ai_system_slug = str(ai_system_snapshot.get("slug", candidate.ai_system.slug))
    prompt_version_label = str(prompt_snapshot.get("version_label", candidate.prompt_version.version_label))
    model_version_label = str(model_snapshot.get("version_label", candidate.model_config.version_label))
    model_name = str(model_snapshot.get("model_name", candidate.model_config.model_name))

    return ":".join(
        [
            ai_system_slug,
            prompt_version_label,
            model_version_label,
            model_name,
            eval_case.eval_dataset.slug,
            eval_case.case_id,
        ]
    )


def simulate_case_result(candidate: ReleaseCandidate, eval_case: EvalCase) -> dict:
    profile = candidate_profile(candidate)
    modifiers = scenario_modifiers(eval_case)
    base_seed = stable_case_seed(candidate, eval_case)

    effective_accuracy = clamp(
        profile["accuracy"] + modifiers["accuracy"],
        0.20,
        0.995,
    )
    schema_probability = clamp(
        profile["schema_valid_rate"] + modifiers["schema"],
        0.20,
        0.999,
    )
    timeout_probability = clamp(
        profile["timeout_rate"] + modifiers["timeout"],
        0.0,
        0.50,
    )
    fallback_probability = clamp(
        profile["fallback_success_rate"] + modifiers["fallback"],
        0.0,
        1.0,
    )

    timeout_roll = stable_ratio(base_seed + ":timeout")
    schema_roll = stable_ratio(base_seed + ":schema")
    fallback_roll = stable_ratio(base_seed + ":fallback")
    latency_roll = stable_ratio(base_seed + ":latency")
    cost_roll = stable_ratio(base_seed + ":cost")
    confidence_roll = stable_ratio(base_seed + ":confidence")

    expected_label = str(eval_case.ground_truth.get("label", "manual_review"))
    timed_out = timeout_roll < timeout_probability
    fallback_used = False

    if timed_out and profile["fallback_enabled"] and fallback_roll < fallback_probability:
        fallback_used = True
        timed_out = False
        execution_status = ExecutionStatus.FALLBACK_USED
    elif timed_out:
        execution_status = ExecutionStatus.TIMEOUT
    else:
        execution_status = ExecutionStatus.SUCCESS

    deterministic_case_bias = (confidence_roll - 0.5) * 0.04
    difficulty_threshold = case_difficulty(eval_case) + deterministic_case_bias
    is_correct = (not timed_out) and (effective_accuracy >= difficulty_threshold)
    schema_valid = (not timed_out) and (schema_roll < schema_probability)

    predicted_label = expected_label if is_correct else alternate_label(expected_label)

    latency_ms = int(
        profile["mean_latency_ms"]
        + modifiers["latency_shift"]
        + ((latency_roll - 0.5) * 420.0)
        + (520.0 if fallback_used else 0.0)
        + (1100.0 if execution_status == ExecutionStatus.TIMEOUT else 0.0)
    )
    latency_ms = max(latency_ms, 150)

    cost_estimate = round(
        profile["mean_cost_estimate"]
        + modifiers["cost_shift"]
        + ((cost_roll - 0.5) * 0.0028)
        + (0.0018 if fallback_used else 0.0),
        4,
    )
    cost_estimate = max(cost_estimate, 0.0001)

    if execution_status == ExecutionStatus.TIMEOUT:
        response_payload = {
            "status": "timeout",
            "message": "Execution exceeded the configured timeout budget.",
        }
        failure_reason = "provider_timeout"
    elif not schema_valid:
        response_payload = {
            "label_text": predicted_label,
            "needs_human_review": bool(eval_case.ground_truth.get("requires_review", False)),
        }
        failure_reason = "response_schema_invalid"
    else:
        response_payload = {
            "label": predicted_label,
            "requires_review": bool(eval_case.ground_truth.get("requires_review", False)),
            "routing_destination": "human_review"
            if eval_case.ground_truth.get("requires_review", False)
            else "automation_queue",
            "confidence": round(0.72 + confidence_roll * 0.24, 3),
        }
        failure_reason = ""

    metric_log = {
        "is_correct": is_correct,
        "schema_valid": schema_valid,
        "latency_ms": latency_ms,
        "cost_estimate": cost_estimate,
        "timed_out": execution_status == ExecutionStatus.TIMEOUT,
        "fallback_used": fallback_used,
        "difficulty_threshold": round(difficulty_threshold, 4),
        "effective_accuracy": round(effective_accuracy, 4),
    }

    return {
        "execution_status": execution_status,
        "expected_label": expected_label,
        "predicted_label": predicted_label if execution_status != ExecutionStatus.TIMEOUT else "",
        "response_payload": response_payload,
        "metric_log": metric_log,
        "failure_reason": failure_reason,
    }


def build_summary_metrics(case_results: list[EvalRunCaseResult]) -> dict:
    total_cases = len(case_results)
    if total_cases == 0:
        return {
            "total_cases": 0,
            "accuracy": 0.0,
            "schema_valid_rate": 0.0,
            "mean_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "mean_cost_estimate": 0.0,
            "timeout_rate": 0.0,
            "fallback_success_rate": 0.0,
        }

    correctness_flags = [result.metric_log.get("is_correct", False) for result in case_results]
    schema_flags = [result.metric_log.get("schema_valid", False) for result in case_results]
    latency_values = [float(result.metric_log.get("latency_ms", 0.0)) for result in case_results]
    cost_values = [float(result.metric_log.get("cost_estimate", 0.0)) for result in case_results]
    timeout_flags = [result.metric_log.get("timed_out", False) for result in case_results]
    fallback_flags = [result.metric_log.get("fallback_used", False) for result in case_results]

    accuracy = sum(1 for value in correctness_flags if value) / total_cases
    schema_valid_rate = sum(1 for value in schema_flags if value) / total_cases
    timeout_rate = sum(1 for value in timeout_flags if value) / total_cases
    fallback_success_rate = sum(1 for value in fallback_flags if value) / total_cases

    return {
        "total_cases": total_cases,
        "accuracy": round(accuracy, 4),
        "schema_valid_rate": round(schema_valid_rate, 4),
        "mean_latency_ms": round(mean(latency_values), 2),
        "p95_latency_ms": round(percentile(latency_values, 95), 2),
        "mean_cost_estimate": round(mean(cost_values), 4),
        "timeout_rate": round(timeout_rate, 4),
        "fallback_success_rate": round(fallback_success_rate, 4),
    }


def build_threshold_results(summary_metrics: dict, threshold_profile: dict) -> dict:
    return {
        "accuracy": {
            "metric_value": summary_metrics["accuracy"],
            "operator": ">=",
            "threshold": threshold_profile["accuracy_min"],
            "passed": summary_metrics["accuracy"] >= threshold_profile["accuracy_min"],
        },
        "schema_valid_rate": {
            "metric_value": summary_metrics["schema_valid_rate"],
            "operator": ">=",
            "threshold": threshold_profile["schema_valid_rate_min"],
            "passed": summary_metrics["schema_valid_rate"] >= threshold_profile["schema_valid_rate_min"],
        },
        "p95_latency_ms": {
            "metric_value": summary_metrics["p95_latency_ms"],
            "operator": "<=",
            "threshold": threshold_profile["p95_latency_ms_max"],
            "passed": summary_metrics["p95_latency_ms"] <= threshold_profile["p95_latency_ms_max"],
        },
        "mean_cost_estimate": {
            "metric_value": summary_metrics["mean_cost_estimate"],
            "operator": "<=",
            "threshold": threshold_profile["mean_cost_estimate_max"],
            "passed": summary_metrics["mean_cost_estimate"] <= threshold_profile["mean_cost_estimate_max"],
        },
        "timeout_rate": {
            "metric_value": summary_metrics["timeout_rate"],
            "operator": "<=",
            "threshold": threshold_profile["timeout_rate_max"],
            "passed": summary_metrics["timeout_rate"] <= threshold_profile["timeout_rate_max"],
        },
    }


def latest_completed_run_for_candidate(
    candidate: ReleaseCandidate,
    dataset_slug: str,
) -> EvalRun | None:
    return (
        candidate.eval_runs.filter(
            eval_dataset__slug=dataset_slug,
            status__in=[EvalRunStatus.PASSED, EvalRunStatus.FAILED],
        )
        .order_by("-completed_at", "-created_at")
        .first()
    )


def comparison_block(current_metrics: dict, baseline_run: EvalRun | None) -> dict:
    if baseline_run is None:
        return {
            "available": False,
            "baseline_run_id": None,
            "summary_metrics": {},
            "delta": {},
        }

    baseline_metrics = baseline_run.summary_metrics or {}
    delta = {}

    for key in [
        "accuracy",
        "schema_valid_rate",
        "mean_latency_ms",
        "p95_latency_ms",
        "mean_cost_estimate",
        "timeout_rate",
        "fallback_success_rate",
    ]:
        current_value = float(current_metrics.get(key, 0.0))
        baseline_value = float(baseline_metrics.get(key, 0.0))
        delta[key] = round(current_value - baseline_value, 4)

    return {
        "available": True,
        "baseline_run_id": baseline_run.id,
        "summary_metrics": baseline_metrics,
        "delta": delta,
    }


def build_comparison_to_baseline(eval_run: EvalRun) -> dict:
    candidate = eval_run.release_candidate
    active_release = candidate.ai_system.active_release
    last_known_good_candidate = (
        ReleaseCandidate.objects.filter(
            ai_system=candidate.ai_system,
            eval_runs__status=EvalRunStatus.PASSED,
        )
        .exclude(id=candidate.id)
        .distinct()
        .order_by("-eval_runs__completed_at", "-eval_runs__created_at")
        .first()
    )

    active_release_run = None
    if active_release and active_release.id != candidate.id:
        active_release_run = latest_completed_run_for_candidate(
            active_release,
            eval_run.eval_dataset.slug,
        )

    last_known_good_run = None
    if last_known_good_candidate and last_known_good_candidate.id != candidate.id:
        last_known_good_run = latest_completed_run_for_candidate(
            last_known_good_candidate,
            eval_run.eval_dataset.slug,
        )

    return {
        "static_thresholds": {
            "available": True,
            "threshold_profile": eval_run.eval_dataset.threshold_profile or DEFAULT_THRESHOLD_PROFILE,
        },
        "active_release": comparison_block(eval_run.summary_metrics, active_release_run),
        "last_known_good_release": comparison_block(eval_run.summary_metrics, last_known_good_run),
    }


@transaction.atomic
def queue_candidate_evals(candidate: ReleaseCandidate, actor, correlation_id: str) -> list[EvalRun]:
    if candidate.status not in {
        ReleaseCandidateStatus.PENDING_EVAL,
        ReleaseCandidateStatus.EVAL_FAILED,
        ReleaseCandidateStatus.PENDING_APPROVAL,
    }:
        raise ValidationError("This release candidate is not eligible to queue evaluation runs.")

    datasets = selected_eval_datasets(candidate)
    run_group = timezone.now().strftime("%Y%m%d%H%M%S")
    run_label_prefix = f"candidate-{candidate.id}-{run_group}"

    candidate.status = ReleaseCandidateStatus.PENDING_EVAL
    candidate.save(update_fields=["status", "updated_at"])

    runs = []
    for dataset in datasets:
        run = EvalRun.objects.create(
            release_candidate=candidate,
            eval_dataset=dataset,
            run_label=f"{run_label_prefix}-{dataset.slug}",
            status=EvalRunStatus.QUEUED,
            correlation_id=correlation_id,
        )
        runs.append(run)

        log_audit_event(
            entity_type="EvalRun",
            entity_id=run.id,
            event_type="queued",
            actor_type=ActorType.USER,
            actor_id=actor.id if actor and actor.is_authenticated else None,
            payload={
                "release_candidate_id": candidate.id,
                "eval_dataset_id": dataset.id,
                "eval_dataset_slug": dataset.slug,
                "run_label": run.run_label,
            },
            correlation_id=correlation_id,
        )

    return runs


def refresh_candidate_status_for_run_group(candidate: ReleaseCandidate, run_label: str) -> ReleaseCandidate:
    prefix = run_label.rsplit("-", 1)[0]
    run_group = candidate.eval_runs.filter(run_label__startswith=prefix).all()

    if run_group.filter(status__in=[EvalRunStatus.QUEUED, EvalRunStatus.RUNNING]).exists():
        candidate.status = ReleaseCandidateStatus.PENDING_EVAL
    else:
        failed_exists = run_group.filter(status=EvalRunStatus.FAILED).exists()
        candidate.status = (
            ReleaseCandidateStatus.EVAL_FAILED
            if failed_exists
            else ReleaseCandidateStatus.PENDING_APPROVAL
        )

    candidate.save(update_fields=["status", "updated_at"])
    return candidate


@transaction.atomic
def evaluate_eval_run(eval_run_id: int, correlation_id: str = "") -> EvalRun:
    eval_run = (
        EvalRun.objects.select_related(
            "release_candidate",
            "release_candidate__ai_system",
            "eval_dataset",
        )
        .prefetch_related("eval_dataset__cases")
        .get(id=eval_run_id)
    )

    eval_run.status = EvalRunStatus.RUNNING
    eval_run.started_at = timezone.now()
    if correlation_id:
        eval_run.correlation_id = correlation_id
    eval_run.save(update_fields=["status", "started_at", "correlation_id", "updated_at"])

    EvalRunCaseResult.objects.filter(eval_run=eval_run).delete()

    created_results = []
    for eval_case in eval_run.eval_dataset.cases.order_by("case_id"):
        simulated = simulate_case_result(eval_run.release_candidate, eval_case)
        created_results.append(
            EvalRunCaseResult.objects.create(
                eval_run=eval_run,
                eval_case=eval_case,
                execution_status=simulated["execution_status"],
                expected_label=simulated["expected_label"],
                predicted_label=simulated["predicted_label"],
                response_payload=simulated["response_payload"],
                metric_log=simulated["metric_log"],
                failure_reason=simulated["failure_reason"],
            )
        )

    summary_metrics = build_summary_metrics(created_results)
    threshold_profile = eval_run.eval_dataset.threshold_profile or DEFAULT_THRESHOLD_PROFILE
    threshold_results = build_threshold_results(summary_metrics, threshold_profile)
    overall_pass = all(result["passed"] for result in threshold_results.values())

    eval_run.summary_metrics = summary_metrics
    eval_run.threshold_results = threshold_results
    eval_run.status = EvalRunStatus.PASSED if overall_pass else EvalRunStatus.FAILED
    eval_run.completed_at = timezone.now()
    eval_run.save(
        update_fields=[
            "summary_metrics",
            "threshold_results",
            "status",
            "completed_at",
            "updated_at",
        ]
    )

    eval_run.comparison_to_baseline = build_comparison_to_baseline(eval_run)
    eval_run.save(update_fields=["comparison_to_baseline", "updated_at"])

    refresh_candidate_status_for_run_group(eval_run.release_candidate, eval_run.run_label)

    log_audit_event(
        entity_type="EvalRun",
        entity_id=eval_run.id,
        event_type="completed",
        actor_type=ActorType.TASK,
        actor_id="evals.evaluate_eval_run_task",
        payload={
            "release_candidate_id": eval_run.release_candidate_id,
            "eval_dataset_id": eval_run.eval_dataset_id,
            "status": eval_run.status,
            "summary_metrics": eval_run.summary_metrics,
            "threshold_results": eval_run.threshold_results,
        },
        correlation_id=correlation_id or eval_run.correlation_id,
    )

    return eval_run
