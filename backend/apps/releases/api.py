from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audits.services import log_audit_event
from apps.core.choices import ActorType

from .models import ReleaseCandidate
from .serializers import ReleaseCandidateSerializer
from .services import submit_release_candidate


class ReleaseCandidateViewSet(viewsets.ModelViewSet):
    queryset = ReleaseCandidate.objects.select_related(
        "ai_system",
        "prompt_version",
        "model_config",
        "created_by",
    ).all()
    serializer_class = ReleaseCandidateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["ai_system", "status"]
    search_fields = ["name", "ai_system__name", "ai_system__slug"]
    ordering_fields = ["created_at", "updated_at", "name", "status"]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        request = self.request
        log_audit_event(
            entity_type="ReleaseCandidate",
            entity_id=instance.id,
            event_type="created",
            actor_type=ActorType.USER,
            actor_id=request.user.id if request.user.is_authenticated else None,
            payload={
                "name": instance.name,
                "status": instance.status,
                "ai_system_id": instance.ai_system_id,
                "prompt_version_id": instance.prompt_version_id,
                "model_config_id": instance.model_config_id,
            },
            correlation_id=getattr(request, "correlation_id", ""),
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        request = self.request
        log_audit_event(
            entity_type="ReleaseCandidate",
            entity_id=instance.id,
            event_type="updated",
            actor_type=ActorType.USER,
            actor_id=request.user.id if request.user.is_authenticated else None,
            payload={
                "name": instance.name,
                "status": instance.status,
                "ai_system_id": instance.ai_system_id,
                "prompt_version_id": instance.prompt_version_id,
                "model_config_id": instance.model_config_id,
            },
            correlation_id=getattr(request, "correlation_id", ""),
        )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        candidate = self.get_object()
        candidate = submit_release_candidate(
            candidate=candidate,
            actor=request.user,
            correlation_id=getattr(request, "correlation_id", ""),
        )
        serializer = self.get_serializer(candidate)
        return Response(serializer.data, status=status.HTTP_200_OK)
