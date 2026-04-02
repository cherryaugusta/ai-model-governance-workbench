from rest_framework import serializers

from .models import AISystem


class AISystemSerializer(serializers.ModelSerializer):
    technical_owner_username = serializers.CharField(source="technical_owner.username", read_only=True)
    business_owner_username = serializers.CharField(source="business_owner.username", read_only=True)
    active_release_id = serializers.SerializerMethodField()

    class Meta:
        model = AISystem
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "owner_team",
            "technical_owner",
            "technical_owner_username",
            "business_owner",
            "business_owner_username",
            "risk_tier",
            "system_type",
            "domain_area",
            "status",
            "active_release_id",
            "created_at",
            "updated_at",
        ]

    def get_active_release_id(self, obj):
        active_release = obj.active_release
        return active_release.id if active_release else None