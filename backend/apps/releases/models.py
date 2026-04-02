from django.core.exceptions import ValidationError
from django.db import models

from apps.core.choices import ReleaseCandidateStatus, RollbackReasonCode
from apps.core.models import TimestampedModel
from apps.model_configs.models import ModelConfig
from apps.prompts.models import PromptVersion
from apps.systems.models import AISystem


class ReleaseCandidate(TimestampedModel):
    ai_system = models.ForeignKey(
        AISystem,
        on_delete=models.CASCADE,
        related_name="release_candidates",
    )
    prompt_version = models.ForeignKey(
        PromptVersion,
        on_delete=models.PROTECT,
        related_name="release_candidates",
    )
    model_config = models.ForeignKey(
        ModelConfig,
        on_delete=models.PROTECT,
        related_name="release_candidates",
    )
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=30,
        choices=ReleaseCandidateStatus.choices,
        default=ReleaseCandidateStatus.DRAFT,
    )
    eval_dataset_ids = models.JSONField(default=list)
    config_snapshot = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="created_release_candidates",
    )

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.prompt_version.ai_system_id != self.ai_system_id:
            raise ValidationError("Prompt version must belong to the same AI system.")
        if self.model_config.ai_system_id != self.ai_system_id:
            raise ValidationError("Model config must belong to the same AI system.")
        if self.prompt_version.status == "retired":
            raise ValidationError("Retired prompt versions cannot be attached to new candidates.")
        if self.model_config.status == "retired":
            raise ValidationError("Retired model configs cannot be attached to new candidates.")

    def save(self, *args, **kwargs):
        if self.pk:
            previous = ReleaseCandidate.objects.get(pk=self.pk)
            immutable_statuses = {
                ReleaseCandidateStatus.PENDING_EVAL,
                ReleaseCandidateStatus.EVAL_FAILED,
                ReleaseCandidateStatus.PENDING_APPROVAL,
                ReleaseCandidateStatus.APPROVED,
                ReleaseCandidateStatus.REJECTED,
                ReleaseCandidateStatus.ACTIVE,
                ReleaseCandidateStatus.ROLLED_BACK,
                ReleaseCandidateStatus.RETIRED,
            }
            if previous.status in immutable_statuses:
                if previous.prompt_version_id != self.prompt_version_id:
                    raise ValidationError("Prompt version cannot change after submission.")
                if previous.model_config_id != self.model_config_id:
                    raise ValidationError("Model config cannot change after submission.")
                if previous.config_snapshot != self.config_snapshot:
                    raise ValidationError("Config snapshot is immutable after submission.")
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.ai_system.slug}:{self.name}"


class PromotionEvent(models.Model):
    ai_system = models.ForeignKey(
        AISystem,
        on_delete=models.CASCADE,
        related_name="promotion_events",
    )
    release_candidate = models.ForeignKey(
        ReleaseCandidate,
        on_delete=models.PROTECT,
        related_name="promotion_events",
    )
    previous_active_candidate = models.ForeignKey(
        ReleaseCandidate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superseded_by_promotions",
    )
    promoted_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="promotion_events",
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Promotion #{self.pk} for {self.ai_system.slug}"


class RollbackRecord(models.Model):
    ai_system = models.ForeignKey(
        AISystem,
        on_delete=models.CASCADE,
        related_name="rollback_records",
    )
    from_candidate = models.ForeignKey(
        ReleaseCandidate,
        on_delete=models.PROTECT,
        related_name="rollback_from_records",
    )
    to_candidate = models.ForeignKey(
        ReleaseCandidate,
        on_delete=models.PROTECT,
        related_name="rollback_to_records",
    )
    reason_code = models.CharField(
        max_length=50,
        choices=RollbackReasonCode.choices,
    )
    comment = models.TextField(blank=True)
    incident = models.ForeignKey(
        "incidents.Incident",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rollback_records",
    )
    rolled_back_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="rollback_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.from_candidate.ai_system_id != self.ai_system_id:
            raise ValidationError("Rollback source candidate must belong to the same AI system.")
        if self.to_candidate.ai_system_id != self.ai_system_id:
            raise ValidationError("Rollback target candidate must belong to the same AI system.")
        if self.from_candidate_id == self.to_candidate_id:
            raise ValidationError("Rollback target must be different from source candidate.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Rollback #{self.pk} for {self.ai_system.slug}"