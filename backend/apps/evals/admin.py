from django.contrib import admin

from .models import EvalCase, EvalDataset, EvalRun


@admin.register(EvalDataset)
class EvalDatasetAdmin(admin.ModelAdmin):
    list_display = ("id", "ai_system", "name", "slug", "scenario_type", "is_active", "created_at")
    search_fields = ("name", "slug", "ai_system__name")
    list_filter = ("scenario_type", "is_active", "ai_system")


@admin.register(EvalCase)
class EvalCaseAdmin(admin.ModelAdmin):
    list_display = ("id", "eval_dataset", "case_id", "created_at")
    search_fields = ("case_id", "eval_dataset__name", "eval_dataset__slug")
    list_filter = ("eval_dataset",)


@admin.register(EvalRun)
class EvalRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "release_candidate",
        "eval_dataset",
        "run_label",
        "status",
        "created_at",
    )
    search_fields = ("run_label", "release_candidate__name")
    list_filter = ("status", "eval_dataset")