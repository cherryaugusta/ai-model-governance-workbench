from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audits.services import log_audit_event
from apps.core.choices import ActorType

from .models import Incident
from .serializers import IncidentResolveSerializer, IncidentSerializer
from .services import resolve_incident


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.select_related(
        "ai_system",
        "release_candidate",
        "reported_by",
    ).all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["ai_system", "release_candidate", "severity", "status", "incident_type"]
    search_fields = ["summary", "description", "ai_system__name", "ai_system__slug"]
    ordering_fields = ["created_at", "updated_at", "severity", "status"]

    def perform_create(self, serializer):
        incident = serializer.save(reported_by=self.request.user)
        request = self.request
        log_audit_event(
            entity_type="Incident",
            entity_id=incident.id,
            event_type="created",
            actor_type=ActorType.USER,
            actor_id=request.user.id if request.user.is_authenticated else None,
            payload={
                "ai_system_id": incident.ai_system_id,
                "release_candidate_id": incident.release_candidate_id,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
                "status": incident.status,
                "summary": incident.summary,
            },
            correlation_id=getattr(request, "correlation_id", ""),
        )

    def perform_update(self, serializer):
        incident = serializer.save()
        request = self.request
        log_audit_event(
            entity_type="Incident",
            entity_id=incident.id,
            event_type="updated",
            actor_type=ActorType.USER,
            actor_id=request.user.id if request.user.is_authenticated else None,
            payload={
                "ai_system_id": incident.ai_system_id,
                "release_candidate_id": incident.release_candidate_id,
                "incident_type": incident.incident_type,
                "severity": incident.severity,
                "status": incident.status,
                "summary": incident.summary,
            },
            correlation_id=getattr(request, "correlation_id", ""),
        )

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        incident = self.get_object()
        payload = IncidentResolveSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        incident = resolve_incident(
            incident=incident,
            actor=request.user,
            resolution_notes=payload.validated_data["resolution_notes"],
            correlation_id=getattr(request, "correlation_id", ""),
        )
        return Response(self.get_serializer(incident).data, status=status.HTTP_200_OK)