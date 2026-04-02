from rest_framework import serializers

from .models import EvalDataset, EvalRun, EvalRunCaseResult


class EvalDatasetSerializer(serializers.ModelSerializer):
    ai_system_name = serializers.CharField(source="ai_system.name", read_only=True)
    case_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = EvalDataset
        fields = [
            "id",
            "ai_system",
            "ai_system_name",
            "name",
            "slug",
            "description",
            "scenario_type",
            "threshold_profile",
            "is_active",
            "case_count",
            "created_at",
            "updated_at",
        ]


class EvalRunCaseResultSerializer(serializers.ModelSerializer):
    case_id = serializers.CharField(source="eval_case.case_id", read_only=True)
    scenario_type = serializers.CharField(source="eval_case.scenario_type", read_only=True)

    class Meta:
        model = EvalRunCaseResult
        fields = [
            "id",
            "case_id",
            "scenario_type",
            "execution_status",
            "expected_label",
            "predicted_label",
            "response_payload",
            "metric_log",
            "failure_reason",
            "created_at",
            "updated_at",
        ]


class EvalRunSerializer(serializers.ModelSerializer):
    release_candidate_name = serializers.CharField(source="release_candidate.name", read_only=True)
    eval_dataset_name = serializers.CharField(source="eval_dataset.name", read_only=True)
    eval_dataset_slug = serializers.CharField(source="eval_dataset.slug", read_only=True)
    case_results = EvalRunCaseResultSerializer(many=True, read_only=True)

    class Meta:
        model = EvalRun
        fields = [
            "id",
            "release_candidate",
            "release_candidate_name",
            "eval_dataset",
            "eval_dataset_name",
            "eval_dataset_slug",
            "run_label",
            "status",
            "summary_metrics",
            "threshold_results",
            "comparison_to_baseline",
            "correlation_id",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
            "case_results",
        ]
