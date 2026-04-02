from django.db import models

from apps.core.choices import AISystemStatus, RiskTier
from apps.core.models import TimestampedModel


class AISystem(TimestampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    owner_team = models.CharField(max_length=255)
    technical_owner = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="technical_systems",
    )
    business_owner = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="business_systems",
    )
    risk_tier = models.CharField(
        max_length=20,
        choices=RiskTier.choices,
        default=RiskTier.MEDIUM,
    )
    system_type = models.CharField(max_length=100)
    domain_area = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=AISystemStatus.choices,
        default=AISystemStatus.DRAFT,
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status", "risk_tier", "owner_team"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def active_release(self):
        return self.release_candidates.filter(
            status="active",
        ).order_by("-created_at").first()