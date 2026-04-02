from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.choices import ApprovalDecision

from .models import ApprovalRecord
from .serializers import ApprovalDecisionSerializer, ApprovalRecordSerializer
from .services import record_approval_decision


class ApprovalRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApprovalRecord.objects.select_related(
        "release_candidate",
        "reviewer",
    ).all()
    serializer_class = ApprovalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["release_candidate", "approval_type", "decision"]
    ordering_fields = ["created_at", "updated_at", "decided_at", "approval_type", "decision"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        approval = self.get_object()
        payload = ApprovalDecisionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        approval = record_approval_decision(
            approval=approval,
            actor=request.user,
            decision=ApprovalDecision.APPROVED,
            comment=payload.validated_data["comment"],
            correlation_id=getattr(request, "correlation_id", ""),
        )
        return Response(self.get_serializer(approval).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        approval = self.get_object()
        payload = ApprovalDecisionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        approval = record_approval_decision(
            approval=approval,
            actor=request.user,
            decision=ApprovalDecision.REJECTED,
            comment=payload.validated_data["comment"],
            correlation_id=getattr(request, "correlation_id", ""),
        )
        return Response(self.get_serializer(approval).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="request-changes")
    def request_changes(self, request, pk=None):
        approval = self.get_object()
        payload = ApprovalDecisionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        approval = record_approval_decision(
            approval=approval,
            actor=request.user,
            decision=ApprovalDecision.CHANGES_REQUESTED,
            comment=payload.validated_data["comment"],
            correlation_id=getattr(request, "correlation_id", ""),
        )
        return Response(self.get_serializer(approval).data, status=status.HTTP_200_OK)
