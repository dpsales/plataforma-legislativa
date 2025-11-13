from django.contrib import admin

from .models import TrackedDocument, TrackedProposition


@admin.register(TrackedDocument)
class TrackedDocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "reference_label", "updated_at")
    search_fields = ("name", "reference_label")
    readonly_fields = ("slug", "created_at", "updated_at")


@admin.register(TrackedProposition)
class TrackedPropositionAdmin(admin.ModelAdmin):
    list_display = (
        "proposition_id",
        "casa",
        "secretaria",
        "titulo",
        "status",
        "updated_at",
    )
    list_filter = ("casa", "secretaria")
    search_fields = ("proposition_id", "titulo", "assunto", "justificativa")
    raw_id_fields = ("document",)
    readonly_fields = ("created_at", "updated_at")
