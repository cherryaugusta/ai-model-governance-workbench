from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audits.services import log_audit_event
from apps.core.choices import ActorType

from .models import PromptVersion
from .serializers import PromptVersionSerializer
from .services import submit_prompt_version


class PromptVersionViewSet(viewsets.ModelViewSet):
    queryset = PromptVersion.objects.select_related(
        "ai_system",
        "created_by",
    ).all()
    serializer_class = PromptVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "ai_system"]
    search_fields = ["name", "version_label", "ai_system__name", "ai_system__slug"]
    ordering_fields = ["created_at", "version_label", "status"]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        request = self.request
        log_audit_event(
            entity_type="PromptVersion",
            entity_id=instance.id,
            event_type="created",
            actor_type=ActorType.USER,
            actor_id=request.user.id if request.user.is_authenticated else None,
            payload={
                "ai_system_id": instance.ai_system_id,
                "version_label": instance.version_label,
                "status": instance.status,
            },
            correlation_id=getattr(request, "correlation_id", ""),
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        request = self.request
        log_audit_event(
            entity_type="PromptVersion",
            entity_id=instance.id,
            event_type="updated",
            actor_type=ActorType.USER,
            actor_id=request.user.id if request.user.is_authenticated else None,
            payload={
                "ai_system_id": instance.ai_system_id,
                "version_label": instance.version_label,
                "status": instance.status,
            },
            correlation_id=getattr(request, "correlation_id", ""),
        )

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        prompt_version = self.get_object()
        try:
            prompt_version = submit_prompt_version(
                prompt_version=prompt_version,
                actor=request.user,
                correlation_id=getattr(request, "correlation_id", ""),
            )
        except DjangoValidationError as exc:
            return Response(
                {"code": "prompt_submit_blocked", "message": str(exc), "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(prompt_version)
        return Response(serializer.data, status=status.HTTP_200_OK)