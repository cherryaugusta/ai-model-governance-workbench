from rest_framework import permissions, viewsets

from apps.audits.services import log_audit_event
from apps.core.choices import ActorType

from .models import AISystem
from .serializers import AISystemSerializer


class AISystemViewSet(viewsets.ModelViewSet):
    queryset = AISystem.objects.select_related(
        "technical_owner",
        "business_owner",
    ).all()
    serializer_class = AISystemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "risk_tier", "owner_team"]
    search_fields = ["name", "slug", "owner_team", "domain_area"]
    ordering_fields = ["created_at", "updated_at", "name", "risk_tier", "status"]

    def perform_create(self, serializer):
        instance = serializer.save()
        request = self.request
        log_audit_event(
            entity_type="AISystem",
            entity_id=instance.id,
            event_type="created",
            actor_type=ActorType.USER,
            actor_id=request.user.id if request.user.is_authenticated else None,
            payload={"name": instance.name, "slug": instance.slug, "status": instance.status},
            correlation_id=getattr(request, "correlation_id", ""),
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        request = self.request
        log_audit_event(
            entity_type="AISystem",
            entity_id=instance.id,
            event_type="updated",
            actor_type=ActorType.USER,
            actor_id=request.user.id if request.user.is_authenticated else None,
            payload={"name": instance.name, "slug": instance.slug, "status": instance.status},
            correlation_id=getattr(request, "correlation_id", ""),
        )