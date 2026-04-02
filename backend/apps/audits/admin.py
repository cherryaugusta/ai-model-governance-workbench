from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "entity_type",
        "entity_id",
        "event_type",
        "actor_type",
        "actor_id",
        "created_at",
    )
    list_filter = ("entity_type", "event_type", "actor_type")
    search_fields = ("entity_type", "entity_id", "event_type", "actor_id")