from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audits.services import log_audit_event
from apps.core.choices import ActorType

from .models import ModelConfig
from .serializers import ModelConfigSerializer
from .services import submit_model_config


class ModelConfigViewSet(viewsets.ModelViewSet):
    queryset = ModelConfig.objects.select_related(
        "ai_system",
        "created_by",
    ).all()
    serializer_class = ModelConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "ai_system", "provider_name"]
    search_fields = ["version_label", "provider_name", "model_name", "ai_system__name"]
    ordering_fields = ["created_at", "version_label", "status", "provider_name"]

    def perform_create(self, serializer):
        instance = serializer.save(created_by=self.request.user)
        request = self.request
        log_audit_event(
            entity_type="ModelConfig",
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
            entity_type="ModelConfig",
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
        model_config = self.get_object()
        try:
            model_config = submit_model_config(
                model_config=model_config,
                actor=request.user,
                correlation_id=getattr(request, "correlation_id", ""),
            )
        except DjangoValidationError as exc:
            return Response(
                {"code": "model_config_submit_blocked", "message": str(exc), "details": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(model_config)
        return Response(serializer.data, status=status.HTTP_200_OK)