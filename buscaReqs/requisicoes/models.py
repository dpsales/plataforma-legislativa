from __future__ import annotations

from django.db import models


class Configuration(models.Model):
    """Stores editable filter options exposed in the Requerimentos module."""

    DEFAULT_NAME = "default"

    name = models.CharField(max_length=64, unique=True, default=DEFAULT_NAME)
    proposition_types = models.JSONField(default=list, blank=True)
    presentation_years = models.JSONField(default=list, blank=True)
    unit_groups = models.JSONField(default=list, blank=True)
    subjects = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - human-readable helper
        return f"Configuração {self.name}"

    @classmethod
    def load(cls) -> "Configuration":
        obj, _ = cls.objects.get_or_create(name=cls.DEFAULT_NAME)
        return obj
