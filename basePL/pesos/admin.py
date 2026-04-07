from django.contrib import admin

from .models import WeightEntry


@admin.register(WeightEntry)
class WeightEntryAdmin(admin.ModelAdmin):
    list_display = ("term", "namespace", "weight", "updated_at")
    list_filter = ("namespace",)
    search_fields = ("term",)
    ordering = ("namespace", "term")
