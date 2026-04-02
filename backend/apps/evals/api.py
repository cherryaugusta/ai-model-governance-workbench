from django.db.models import Count
from rest_framework import permissions, viewsets

from .models import EvalDataset, EvalRun
from .serializers import EvalDatasetSerializer, EvalRunSerializer


class EvalDatasetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        EvalDataset.objects.select_related("ai_system")
        .annotate(case_count=Count("cases"))
        .all()
    )
    serializer_class = EvalDatasetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["ai_system", "scenario_type", "is_active"]
    search_fields = ["name", "slug", "ai_system__name", "ai_system__slug"]
    ordering_fields = ["name", "created_at", "scenario_type"]


class EvalRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        EvalRun.objects.select_related(
            "release_candidate",
            "release_candidate__ai_system",
            "eval_dataset",
        )
        .prefetch_related("case_results", "case_results__eval_case")
        .all()
    )
    serializer_class = EvalRunSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["release_candidate", "eval_dataset", "status"]
    search_fields = [
        "run_label",
        "release_candidate__name",
        "release_candidate__ai_system__name",
        "eval_dataset__name",
        "eval_dataset__slug",
    ]
    ordering_fields = ["created_at", "completed_at", "status", "run_label"]
