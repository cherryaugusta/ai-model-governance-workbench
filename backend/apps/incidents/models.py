from django.db import models

from apps.core.choices import IncidentSeverity, IncidentStatus, IncidentType
from apps.core.models import TimestampedModel
from apps.releases.models import ReleaseCandidate
from apps.systems.models import AISystem


class Incident(TimestampedModel):
    ai_system = models.ForeignKey(
        AISystem,
        on_delete=models.CASCADE,
        related_name="incidents",
    )
    release_candidate = models.ForeignKey(
        ReleaseCandidate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents",
    )
    incident_type = models.CharField(max_length=50, choices=IncidentType.choices)
    severity = models.CharField(max_length=20, choices=IncidentSeverity.choices)
    status = models.CharField(
        max_length=20,
        choices=IncidentStatus.choices,
        default=IncidentStatus.OPEN,
    )
    summary = models.CharField(max_length=255)
    description = models.TextField()
    reported_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="reported_incidents",
    )
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "severity", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.summary