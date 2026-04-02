from rest_framework import permissions, viewsets

from .models import AuditEvent
from .serializers import AuditEventSerializer


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.all()
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["entity_type", "event_type", "actor_type"]
    search_fields = ["entity_type", "entity_id", "event_type", "correlation_id"]
    ordering_fields = ["created_at", "entity_type", "event_type", "actor_type"]