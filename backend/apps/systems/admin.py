from django.contrib import admin

from .models import AISystem


@admin.register(AISystem)
class AISystemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
        "owner_team",
        "risk_tier",
        "status",
        "created_at",
    )
    search_fields = ("name", "slug", "owner_team", "domain_area")
    list_filter = ("risk_tier", "status", "owner_team")