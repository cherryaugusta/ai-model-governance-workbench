from rest_framework import serializers

from apps.approvals.services import approval_summary, required_approval_types_for_risk
from apps.core.choices import ReleaseCandidateStatus

from .models import ReleaseCandidate


class ReleaseCandidateSerializer(serializers.ModelSerializer):
    ai_system_name = serializers.CharField(source="ai_system.name", read_only=True)
    prompt_version_label = serializers.CharField(source="prompt_version.version_label", read_only=True)
    model_config_version_label = serializers.CharField(source="model_config.version_label", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    can_submit = serializers.SerializerMethodField()
    can_run_evals = serializers.SerializerMethodField()
    can_request_approval = serializers.SerializerMethodField()
    required_approval_types = serializers.SerializerMethodField()
    approval_summary = serializers.SerializerMethodField()
    blocking_reasons = serializers.SerializerMethodField()

    class Meta:
        model = ReleaseCandidate
        fields = [
            "id",
            "ai_system",
            "ai_system_name",
            "prompt_version",
            "prompt_version_label",
            "model_config",
            "model_config_version_label",
            "name",
            "status",
            "eval_dataset_ids",
            "config_snapshot",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
            "can_submit",
            "can_run_evals",
            "can_request_approval",
            "required_approval_types",
            "approval_summary",
            "blocking_reasons",
        ]
        read_only_fields = [
            "status",
            "config_snapshot",
            "created_by",
            "created_by_username",
            "ai_system_name",
            "prompt_version_label",
            "model_config_version_label",
            "created_at",
            "updated_at",
            "can_submit",
            "can_run_evals",
            "can_request_approval",
            "required_approval_types",
            "approval_summary",
            "blocking_reasons",
        ]

    def validate(self, attrs):
        ai_system = attrs.get("ai_system") or getattr(self.instance, "ai_system", None)
        prompt_version = attrs.get("prompt_version") or getattr(self.instance, "prompt_version", None)
        model_config = attrs.get("model_config") or getattr(self.instance, "model_config", None)

        if ai_system and prompt_version and prompt_version.ai_system_id != ai_system.id:
            raise serializers.ValidationError(
                {"prompt_version": "Prompt version must belong to the same AI system."}
            )

        if ai_system and model_config and model_config.ai_system_id != ai_system.id:
            raise serializers.ValidationError(
                {"model_config": "Model config must belong to the same AI system."}
            )

        return attrs

    def get_can_submit(self, obj):
        return obj.status == ReleaseCandidateStatus.DRAFT

    def get_can_run_evals(self, obj):
        return obj.status in {
            ReleaseCandidateStatus.PENDING_EVAL,
            ReleaseCandidateStatus.EVAL_FAILED,
            ReleaseCandidateStatus.PENDING_APPROVAL,
        }

    def get_can_request_approval(self, obj):
        return obj.status == ReleaseCandidateStatus.PENDING_APPROVAL

    def get_required_approval_types(self, obj):
        return required_approval_types_for_risk(obj.ai_system.risk_tier)

    def get_approval_summary(self, obj):
        return approval_summary(obj)

    def get_blocking_reasons(self, obj):
        reasons = []

        if obj.status == ReleaseCandidateStatus.DRAFT:
            reasons.append("candidate_not_submitted")

        if not obj.config_snapshot:
            reasons.append("snapshot_not_created")

        if obj.prompt_version.status == "retired":
            reasons.append("prompt_version_retired")

        if obj.model_config.status == "retired":
            reasons.append("model_config_retired")

        if obj.status == ReleaseCandidateStatus.PENDING_EVAL:
            reasons.append("awaiting_eval_results")

        if obj.status == ReleaseCandidateStatus.EVAL_FAILED:
            reasons.append("latest_eval_failed")

        if obj.status == ReleaseCandidateStatus.PENDING_APPROVAL:
            summary = approval_summary(obj)

            if summary["missing_types"]:
                reasons.append("approval_queue_not_initialized")
            elif not summary["is_complete"]:
                reasons.append("required_approvals_incomplete")

        return reasons
