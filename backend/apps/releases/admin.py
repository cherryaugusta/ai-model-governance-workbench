from django.contrib import admin

from .models import PromotionEvent, ReleaseCandidate, RollbackRecord


@admin.register(ReleaseCandidate)
class ReleaseCandidateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ai_system",
        "name",
        "status",
        "prompt_version",
        "model_config",
        "created_by",
        "created_at",
    )
    search_fields = ("name", "ai_system__name", "ai_system__slug")
    list_filter = ("status", "ai_system")


@admin.register(PromotionEvent)
class PromotionEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ai_system",
        "release_candidate",
        "previous_active_candidate",
        "promoted_by",
        "created_at",
    )
    list_filter = ("ai_system",)


@admin.register(RollbackRecord)
class RollbackRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ai_system",
        "from_candidate",
        "to_candidate",
        "reason_code",
        "rolled_back_by",
        "created_at",
    )
    list_filter = ("ai_system", "reason_code")