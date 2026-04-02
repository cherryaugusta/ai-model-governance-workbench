from rest_framework import serializers

from .models import ApprovalRecord


class ApprovalRecordSerializer(serializers.ModelSerializer):
    release_candidate_name = serializers.CharField(source="release_candidate.name", read_only=True)
    reviewer_username = serializers.CharField(source="reviewer.username", read_only=True)

    class Meta:
        model = ApprovalRecord
        fields = [
            "id",
            "release_candidate",
            "release_candidate_name",
            "approval_type",
            "reviewer",
            "reviewer_username",
            "decision",
            "comment",
            "decided_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "release_candidate_name",
            "reviewer",
            "reviewer_username",
            "decision",
            "comment",
            "decided_at",
            "created_at",
            "updated_at",
        ]


class ApprovalDecisionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, default="")
