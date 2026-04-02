from rest_framework import serializers

from .models import Incident


class IncidentSerializer(serializers.ModelSerializer):
    ai_system_name = serializers.CharField(source="ai_system.name", read_only=True)
    release_candidate_name = serializers.CharField(
        source="release_candidate.name",
        read_only=True,
    )
    reported_by_username = serializers.CharField(
        source="reported_by.username",
        read_only=True,
    )

    class Meta:
        model = Incident
        fields = [
            "id",
            "ai_system",
            "ai_system_name",
            "release_candidate",
            "release_candidate_name",
            "incident_type",
            "severity",
            "status",
            "summary",
            "description",
            "reported_by",
            "reported_by_username",
            "resolution_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "reported_by",
            "reported_by_username",
            "ai_system_name",
            "release_candidate_name",
            "created_at",
            "updated_at",
        ]


class IncidentResolveSerializer(serializers.Serializer):
    resolution_notes = serializers.CharField(required=False, allow_blank=True, default="")