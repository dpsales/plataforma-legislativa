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


class Requerimento(models.Model):
    """Armazena requerimentos e proposições de interesse."""

    titulo = models.CharField(max_length=500)
    autor = models.CharField(max_length=300, blank=True, null=True)
    ementa = models.TextField(blank=True, null=True)
    situacao = models.CharField(max_length=200, blank=True, null=True)
    data_apresentacao = models.DateField(blank=True, null=True)
    data_ultima_tramitacao = models.DateField(blank=True, null=True)
    descricao_ultima_tramitacao = models.TextField(blank=True, null=True)
    link_ficha = models.URLField(blank=True, null=True)
    link_inteiro_teor = models.URLField(blank=True, null=True)
    termos_encontrados = models.CharField(max_length=500, blank=True, null=True)
    grupos_encontrados = models.CharField(max_length=500, blank=True, null=True)
    assuntos_encontrados = models.CharField(max_length=500, blank=True, null=True)
    local = models.CharField(max_length=300, blank=True, null=True)
    casa = models.CharField(max_length=100, blank=True, null=True)
    
    # Campo único para evitar duplicatas
    codigo_material = models.CharField(max_length=100, unique=True, db_index=True)
    
    data_insercao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_ultima_tramitacao", "-data_apresentacao"]
        verbose_name = "Requerimento"
        verbose_name_plural = "Requerimentos"
        indexes = [
            models.Index(fields=["-data_ultima_tramitacao"]),
            models.Index(fields=["casa"]),
        ]

    def __str__(self) -> str:
        return f"{self.codigo_material} - {self.titulo}"
