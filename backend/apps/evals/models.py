from django.db import models

from apps.core.choices import EvalRunStatus, ExecutionStatus
from apps.core.models import TimestampedModel
from apps.releases.models import ReleaseCandidate


class EvalDataset(TimestampedModel):
    ai_system = models.ForeignKey(
        "systems.AISystem",
        on_delete=models.CASCADE,
        related_name="eval_datasets",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    scenario_type = models.CharField(max_length=100)
    threshold_profile = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("ai_system", "slug")]
        indexes = [
            models.Index(fields=["ai_system", "scenario_type", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.ai_system.slug}:{self.slug}"


class EvalCase(TimestampedModel):
    eval_dataset = models.ForeignKey(
        EvalDataset,
        on_delete=models.CASCADE,
        related_name="cases",
    )
    case_id = models.CharField(max_length=100)
    scenario_type = models.CharField(max_length=100, blank=True, default="")
    input_payload = models.JSONField(default=dict)
    ground_truth = models.JSONField(default=dict)
    expected_metrics = models.JSONField(default=dict)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["case_id"]
        unique_together = [("eval_dataset", "case_id")]
        indexes = [
            models.Index(fields=["eval_dataset", "scenario_type"]),
        ]

    def __str__(self) -> str:
        return self.case_id


class EvalRun(TimestampedModel):
    release_candidate = models.ForeignKey(
        ReleaseCandidate,
        on_delete=models.CASCADE,
        related_name="eval_runs",
    )
    eval_dataset = models.ForeignKey(
        EvalDataset,
        on_delete=models.PROTECT,
        related_name="eval_runs",
    )
    run_label = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=EvalRunStatus.choices,
        default=EvalRunStatus.QUEUED,
    )
    summary_metrics = models.JSONField(default=dict)
    threshold_results = models.JSONField(default=dict)
    comparison_to_baseline = models.JSONField(default=dict)
    correlation_id = models.CharField(max_length=100, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["release_candidate", "created_at"]),
            models.Index(fields=["run_label", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"EvalRun #{self.pk} ({self.status})"


class EvalRunCaseResult(TimestampedModel):
    eval_run = models.ForeignKey(
        EvalRun,
        on_delete=models.CASCADE,
        related_name="case_results",
    )
    eval_case = models.ForeignKey(
        EvalCase,
        on_delete=models.PROTECT,
        related_name="run_results",
    )
    execution_status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.SUCCESS,
    )
    expected_label = models.CharField(max_length=100, blank=True)
    predicted_label = models.CharField(max_length=100, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    metric_log = models.JSONField(default=dict, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["eval_case__case_id"]
        unique_together = [("eval_run", "eval_case")]
        indexes = [
            models.Index(fields=["eval_run", "execution_status"]),
            models.Index(fields=["eval_run", "eval_case"]),
        ]

    def __str__(self) -> str:
        return f"{self.eval_run_id}:{self.eval_case.case_id}"
