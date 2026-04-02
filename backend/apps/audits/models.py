from django.core.exceptions import ValidationError
from django.db import models

from apps.core.choices import ActorType


class AuditEvent(models.Model):
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    event_type = models.CharField(max_length=100)
    actor_type = models.CharField(max_length=20, choices=ActorType.choices)
    actor_id = models.CharField(max_length=100, blank=True)
    payload = models.JSONField(default=dict)
    correlation_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "event_type", "created_at"]),
            models.Index(fields=["actor_type", "created_at"]),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("Audit events are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.entity_type}:{self.event_type}:{self.entity_id}"