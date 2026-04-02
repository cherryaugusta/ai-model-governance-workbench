from django.contrib import admin

from .models import ApprovalRecord


@admin.register(ApprovalRecord)
class ApprovalRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "release_candidate",
        "approval_type",
        "decision",
        "reviewer",
        "decided_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("approval_type", "decision")
    search_fields = ("release_candidate__name", "reviewer__username")
