from django.db import models
from django.utils import timezone

from apps.core.choices import ApprovalDecision, ApprovalType
from apps.core.models import TimestampedModel
from apps.releases.models import ReleaseCandidate


class ApprovalRecord(TimestampedModel):
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
        null=True,
        blank=True,
    )
    decision = models.CharField(
        max_length=30,
        choices=ApprovalDecision.choices,
        default=ApprovalDecision.PENDING,
    )
    comment = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["release_candidate_id", "approval_type"]
        unique_together = [("release_candidate", "approval_type")]
        indexes = [
            models.Index(fields=["approval_type", "decision", "created_at"]),
            models.Index(fields=["release_candidate", "decision", "approval_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.release_candidate_id}:{self.approval_type}:{self.decision}"

    def mark_decided(self):
        self.decided_at = timezone.now()
