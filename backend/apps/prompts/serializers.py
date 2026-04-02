from rest_framework import serializers

from .models import PromptVersion


class PromptVersionSerializer(serializers.ModelSerializer):
    ai_system_name = serializers.CharField(source="ai_system.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = PromptVersion
        fields = [
            "id",
            "ai_system",
            "ai_system_name",
            "name",
            "purpose",
            "version_label",
            "status",
            "template_text",
            "schema_version",
            "input_contract",
            "output_contract",
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