from django.db import models


class Proposition(models.Model):
    proposition_id = models.CharField(max_length=64, unique=True)
    sigla_tipo = models.CharField(max_length=16, blank=True)
    numero = models.CharField(max_length=16, blank=True)
    ano = models.CharField(max_length=8, blank=True)
    proposicao = models.CharField(max_length=64, blank=True)
    autor = models.CharField(max_length=255, blank=True)
    ementa = models.TextField(blank=True)
    situacao_sigla = models.CharField(max_length=64, blank=True)
    situacao = models.CharField(max_length=255, blank=True)
    comissao = models.CharField(max_length=128, blank=True)
    data_situacao_recente = models.DateTimeField(null=True, blank=True)
    historico = models.TextField(blank=True)
    textos_associados = models.JSONField(default=list, blank=True)
    ficha_tramitacao_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_situacao_recente", "-updated_at"]
        indexes = [
            models.Index(fields=["proposition_id"]),
            models.Index(fields=["sigla_tipo"]),
            models.Index(fields=["comissao"]),
            models.Index(fields=["situacao"]),
        ]

    def __str__(self) -> str:
        return self.proposicao or self.proposition_id
