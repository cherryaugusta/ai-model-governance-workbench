from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.approvals.services import request_candidate_approval
from apps.audits.services import log_audit_event
from apps.core.choices import ActorType
from apps.evals.services import queue_candidate_evals
from apps.evals.tasks import evaluate_eval_run_task

from .models import ReleaseCandidate
from .serializers import (
    ReleaseCandidateSerializer,
    ReleasePromotionSerializer,
    ReleaseRollbackSerializer,
)
from .services import (
    promote_candidate,
    rollback_release_candidate,
    submit_release_candidate,
)


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

    @action(detail=True, methods=["post"], url_path="run-evals")
    def run_evals(self, request, pk=None):
        candidate = self.get_object()
        correlation_id = getattr(request, "correlation_id", "")
        queued_runs = queue_candidate_evals(
            candidate=candidate,
            actor=request.user,
            correlation_id=correlation_id,
        )

        for run in queued_runs:
            evaluate_eval_run_task.delay(run.id, correlation_id)

        serializer = self.get_serializer(candidate)
        return Response(
            {
                "release_candidate": serializer.data,
                "queued_eval_run_ids": [run.id for run in queued_runs],
                "run_label": queued_runs[0].run_label.rsplit("-", 1)[0] if queued_runs else "",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"], url_path="request-approval")
    def request_approval(self, request, pk=None):
        candidate = self.get_object()
        approvals = request_candidate_approval(
            candidate=candidate,
            actor=request.user,
            correlation_id=getattr(request, "correlation_id", ""),
        )
        serializer = self.get_serializer(candidate)
        return Response(
            {
                "release_candidate": serializer.data,
                "approval_record_ids": [approval.id for approval in approvals],
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def promote(self, request, pk=None):
        candidate = self.get_object()
        payload = ReleasePromotionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        candidate = promote_candidate(
            candidate=candidate,
            actor=request.user,
            reason=payload.validated_data["reason"],
            correlation_id=getattr(request, "correlation_id", ""),
        )

        return Response(
            self.get_serializer(candidate).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def rollback(self, request, pk=None):
        candidate = self.get_object()
        payload = ReleaseRollbackSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        result = rollback_release_candidate(
            candidate=candidate,
            actor=request.user,
            reason_code=payload.validated_data["reason_code"],
            comment=payload.validated_data["comment"],
            correlation_id=getattr(request, "correlation_id", ""),
        )

        return Response(
            {
                "from_candidate": self.get_serializer(result["from_candidate"]).data,
                "to_candidate": self.get_serializer(result["to_candidate"]).data,
                "rollback_record_id": result["rollback_record"].id,
            },
            status=status.HTTP_200_OK,
        )