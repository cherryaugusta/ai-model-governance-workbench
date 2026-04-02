from django.contrib import admin

from .models import ModelConfig


@admin.register(ModelConfig)
class ModelConfigAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ai_system",
        "version_label",
        "provider_name",
        "model_name",
        "status",
        "created_by",
        "created_at",
    )
    search_fields = ("version_label", "provider_name", "model_name", "ai_system__name")
    list_filter = ("status", "provider_name", "ai_system")