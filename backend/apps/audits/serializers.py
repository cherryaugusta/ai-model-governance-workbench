from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "entity_type",
            "entity_id",
            "event_type",
            "actor_type",
            "actor_id",
            "payload",
            "correlation_id",
            "created_at",
        ]
        read_only_fields = fields