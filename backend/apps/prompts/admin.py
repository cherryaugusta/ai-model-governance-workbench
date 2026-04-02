from django.contrib import admin

from .models import PromptVersion


@admin.register(PromptVersion)
class PromptVersionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ai_system",
        "name",
        "version_label",
        "status",
        "created_by",
        "created_at",
    )
    search_fields = ("name", "version_label", "ai_system__name", "ai_system__slug")
    list_filter = ("status", "ai_system")