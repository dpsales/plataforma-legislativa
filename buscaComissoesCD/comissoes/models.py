from django.db import models


class CommissionSelection(models.Model):
    DEFAULT_NAME = "default"

    name = models.CharField(max_length=64, unique=True, default=DEFAULT_NAME)
    siglas = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Seleção de comissões"
        verbose_name_plural = "Seleções de comissões"

    def __str__(self) -> str:  # pragma: no cover - representação simples
        return f"{self.name} ({len(self.siglas or [])} selecionadas)"


class Proposition(models.Model):
    proposition_id = models.CharField(max_length=64, unique=True)
    sigla_tipo = models.CharField(max_length=16)
    numero = models.CharField(max_length=16)
    ano = models.CharField(max_length=8)
    proposicao = models.CharField(max_length=64)
    autor = models.CharField(max_length=255, blank=True)
    ementa = models.TextField(blank=True)
    situacao = models.CharField(max_length=255, blank=True)
    situacao_tramitacao = models.CharField(max_length=255, blank=True)
    orgao_sigla = models.CharField(max_length=64, blank=True)
    inteiro_teor_url = models.URLField(blank=True)
    ficha_tramitacao_url = models.URLField(blank=True)
    data_apresentacao = models.DateField(null=True, blank=True)
    data_ultima_tramitacao = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_ultima_tramitacao", "-updated_at"]
        indexes = [
            models.Index(fields=["sigla_tipo"]),
            models.Index(fields=["orgao_sigla"]),
            models.Index(fields=["proposition_id"]),
        ]

    def __str__(self) -> str:  # pragma: no cover - str helper
        return self.proposicao
