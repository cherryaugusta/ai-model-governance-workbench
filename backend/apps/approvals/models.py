from django.db import models

from apps.core.choices import ApprovalDecision, ApprovalType
from apps.releases.models import ReleaseCandidate


class ApprovalRecord(models.Model):
    release_candidate = models.ForeignKey(
        ReleaseCandidate,
        on_delete=models.CASCADE,
        related_name="approval_records",
    )
    approval_type = models.CharField(max_length=30, choices=ApprovalType.choices)
    reviewer = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="approval_records",
    )
    decision = models.CharField(
        max_length=30,
        choices=ApprovalDecision.choices,
        default=ApprovalDecision.PENDING,
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["approval_type", "decision", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.approval_type}:{self.decision}"