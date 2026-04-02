from django.db import models

from apps.core.choices import ExecutionStatus
from apps.evals.models import EvalRun


class ModelExecutionLog(models.Model):
    eval_run = models.ForeignKey(
        EvalRun,
        on_delete=models.CASCADE,
        related_name="execution_logs",
    )
    provider_name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    prompt_version = models.CharField(max_length=100)
    latency_ms = models.PositiveIntegerField()
    input_token_estimate = models.PositiveIntegerField(default=0)
    output_token_estimate = models.PositiveIntegerField(default=0)
    cost_estimate = models.DecimalField(max_digits=8, decimal_places=4, default=0.0)
    status = models.CharField(max_length=30, choices=ExecutionStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"ExecutionLog #{self.pk} ({self.status})"