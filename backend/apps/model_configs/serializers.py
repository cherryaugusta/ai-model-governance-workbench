from rest_framework import serializers

from .models import ModelConfig


class ModelConfigSerializer(serializers.ModelSerializer):
    ai_system_name = serializers.CharField(source="ai_system.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = ModelConfig
        fields = [
            "id",
            "ai_system",
            "ai_system_name",
            "version_label",
            "provider_name",
            "model_name",
            "temperature",
            "max_tokens",
            "top_p",
            "timeout_ms",
            "routing_policy",
            "fallback_policy",
            "cost_budget_per_run",
            "status",
            "created_by",
            "created_by_username",
            "created_at",
        ]
        read_only_fields = ["status", "created_at"]

    def create(self, validated_data):
        if "created_by" not in validated_data:
            request = self.context.get("request")
            if request and request.user and request.user.is_authenticated:
                validated_data["created_by"] = request.user
        return super().create(validated_data)