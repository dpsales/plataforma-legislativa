from __future__ import annotations

from django.db import models


class CasaChoices(models.TextChoices):
    CAMARA = "CD", "Câmara dos Deputados"
    SENADO = "SF", "Senado Federal"


class Proposition(models.Model):
    identifier = models.CharField(max_length=128, unique=True)
    casa = models.CharField(max_length=2, choices=CasaChoices.choices)
    sigla_tipo = models.CharField(max_length=16, blank=True)
    numero = models.CharField(max_length=16, blank=True)
    ano = models.CharField(max_length=8, blank=True)
    ementa = models.TextField(blank=True)
    justificativa = models.TextField(blank=True, default="")
    autor = models.CharField(max_length=255, blank=True)
    autor_partido_uf = models.CharField(max_length=255, blank=True)
    link_inteiro_teor = models.URLField(blank=True)
    link_ficha = models.URLField(blank=True)
    tem_pl = models.BooleanField(default=False)
    impacto_fiscal = models.CharField(max_length=255, blank=True)
    impacto_categoria = models.CharField(max_length=255, blank=True)
    palavras_chave = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["casa", "sigla_tipo", "numero", "ano"]

    def __str__(self) -> str:
        return self.identifier


class Event(models.Model):
    external_id = models.CharField(max_length=128)
    proposition = models.ForeignKey(Proposition, on_delete=models.CASCADE, related_name="events")
    casa = models.CharField(max_length=2, choices=CasaChoices.choices)
    colegiado = models.CharField(max_length=255)
    data_evento = models.DateField(null=True, blank=True)
    hora_evento = models.CharField(max_length=16, blank=True)
    link_colegiado = models.URLField(blank=True)
    plenario_ou_comissao = models.CharField(max_length=64, blank=True)
    marcar_para_relatorio = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-data_evento", "-criado_em"]
        unique_together = ("external_id", "proposition")

    def __str__(self) -> str:
        return f"{self.external_id} | {self.proposition_id}"


class MonitoredProposition(models.Model):
    proposition = models.OneToOneField(Proposition, on_delete=models.CASCADE, related_name="monitoramento")
    prioridade = models.PositiveIntegerField(default=0)
    destaque = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True)
    selecionado_por = models.CharField(max_length=64, blank=True)
    selecionado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-destaque", "-prioridade", "proposition__identifier"]

    def __str__(self) -> str:
        return f"Monitoramento {self.proposition_id}"


class Tramitacao(models.Model):
    monitored = models.ForeignKey(MonitoredProposition, on_delete=models.CASCADE, related_name="tramitacoes")
    data = models.DateTimeField()
    descricao = models.TextField()
    origem = models.CharField(max_length=255, blank=True)
    link = models.URLField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-criado_em"]

    def __str__(self) -> str:
        return f"{self.monitored_id} @ {self.data:%Y-%m-%d}"
