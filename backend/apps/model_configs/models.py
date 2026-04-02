from django.db import models

from apps.core.choices import ArtefactStatus
from apps.systems.models import AISystem


class ModelConfig(models.Model):
    ai_system = models.ForeignKey(
        AISystem,
        on_delete=models.CASCADE,
        related_name="model_configs",
    )
    version_label = models.CharField(max_length=100)
    provider_name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    temperature = models.DecimalField(max_digits=4, decimal_places=2, default=0.20)
    max_tokens = models.PositiveIntegerField(default=512)
    top_p = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    timeout_ms = models.PositiveIntegerField(default=2500)
    routing_policy = models.JSONField(default=dict)
    fallback_policy = models.JSONField(default=dict)
    cost_budget_per_run = models.DecimalField(max_digits=8, decimal_places=4, default=0.0200)
    status = models.CharField(
        max_length=20,
        choices=ArtefactStatus.choices,
        default=ArtefactStatus.DRAFT,
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="created_model_configs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ai_system_id", "-created_at"]
        unique_together = [("ai_system", "version_label")]

    def __str__(self) -> str:
        return f"{self.ai_system.slug}:{self.version_label}"