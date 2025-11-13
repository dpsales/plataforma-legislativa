from __future__ import annotations

from django.db import models


class TrackedDocument(models.Model):
    DEFAULT_SLUG = "default"

    slug = models.SlugField(max_length=64, unique=True, default=DEFAULT_SLUG)
    name = models.CharField(max_length=120, default="Documento de acompanhamento")
    description = models.TextField(blank=True)
    reference_label = models.CharField(max_length=120, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    last_updated_profile = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documento monitorado"
        verbose_name_plural = "Documentos monitorados"

    def __str__(self) -> str:  # pragma: no cover - representação simples
        return self.name


class TrackedProposition(models.Model):
    CASA_CAMARA = "camara"
    CASA_SENADO = "senado"
    CASA_CHOICES = [
        (CASA_CAMARA, "Câmara"),
        (CASA_SENADO, "Senado"),
    ]

    document = models.ForeignKey(
        TrackedDocument,
        on_delete=models.CASCADE,
        related_name="propositions",
    )
    proposition_id = models.BigIntegerField()
    casa = models.CharField(max_length=16, choices=CASA_CHOICES)
    secretaria = models.CharField(max_length=120, blank=True)
    tipo_sigla = models.CharField(max_length=20, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    ano = models.PositiveIntegerField(null=True, blank=True)
    assunto = models.CharField(max_length=255, blank=True)
    prioridade = models.IntegerField(null=True, blank=True)
    justificativa = models.TextField(blank=True)

    titulo = models.CharField(max_length=255, blank=True)
    ementa = models.TextField(blank=True)
    autor = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=255, blank=True)
    ultima_movimentacao = models.TextField(blank=True)
    data_movimentacao = models.DateTimeField(null=True, blank=True)
    link_ficha = models.URLField(blank=True)
    link_inteiro_teor = models.URLField(blank=True)
    fonte = models.CharField(max_length=16, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_movimentacao", "-updated_at"]
        unique_together = [
            ("document", "proposition_id"),
        ]
        indexes = [
            models.Index(fields=["document", "casa"]),
            models.Index(fields=["document", "secretaria"]),
            models.Index(fields=["document", "prioridade"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - representação simples
        return f"{self.proposition_id} ({self.get_casa_display()})"

    @property
    def casa_display(self) -> str:
        return self.get_casa_display()
