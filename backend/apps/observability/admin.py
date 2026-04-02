from django.contrib import admin

from .models import ModelExecutionLog


@admin.register(ModelExecutionLog)
class ModelExecutionLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "eval_run",
        "provider_name",
        "model_name",
        "prompt_version",
        "latency_ms",
        "cost_estimate",
        "status",
        "created_at",
    )
    list_filter = ("provider_name", "model_name", "status")
    search_fields = ("provider_name", "model_name", "prompt_version")