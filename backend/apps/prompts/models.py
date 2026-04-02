from django.db import models

from apps.core.choices import ArtefactStatus
from apps.systems.models import AISystem


class PromptVersion(models.Model):
    ai_system = models.ForeignKey(
        AISystem,
        on_delete=models.CASCADE,
        related_name="prompt_versions",
    )
    name = models.CharField(max_length=255)
    purpose = models.TextField(blank=True)
    version_label = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=ArtefactStatus.choices,
        default=ArtefactStatus.DRAFT,
    )
    template_text = models.TextField()
    schema_version = models.CharField(max_length=50, default="1.0")
    input_contract = models.JSONField(default=dict)
    output_contract = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="created_prompt_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ai_system_id", "-created_at"]
        unique_together = [("ai_system", "version_label")]

    def __str__(self) -> str:
        return f"{self.ai_system.slug}:{self.version_label}"