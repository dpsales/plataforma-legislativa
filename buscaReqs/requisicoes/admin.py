from django.contrib import admin

from .models import Configuration


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
	list_display = ("name", "updated_at")
	readonly_fields = ("updated_at",)
	search_fields = ("name",)
