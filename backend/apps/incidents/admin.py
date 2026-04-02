from django.contrib import admin

from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ai_system",
        "release_candidate",
        "incident_type",
        "severity",
        "status",
        "reported_by",
        "created_at",
    )
    list_filter = ("incident_type", "severity", "status")
    search_fields = ("summary", "ai_system__name")