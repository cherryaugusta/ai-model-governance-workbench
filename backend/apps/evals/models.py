from django.db import models

from apps.core.choices import EvalRunStatus
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
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("ai_system", "slug")]

    def __str__(self) -> str:
        return f"{self.ai_system.slug}:{self.slug}"


class EvalCase(models.Model):
    eval_dataset = models.ForeignKey(
        EvalDataset,
        on_delete=models.CASCADE,
        related_name="cases",
    )
    case_id = models.CharField(max_length=100)
    input_payload = models.JSONField(default=dict)
    ground_truth = models.JSONField(default=dict)
    expected_metrics = models.JSONField(default=dict)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["case_id"]
        unique_together = [("eval_dataset", "case_id")]

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
        ]

    def __str__(self) -> str:
        return f"EvalRun #{self.pk} ({self.status})"