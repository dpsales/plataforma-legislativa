from django.contrib import admin

from .models import Event, MonitoredProposition, Proposition, Tramitacao


@admin.register(Proposition)
class PropositionAdmin(admin.ModelAdmin):
    list_display = ("identifier", "casa", "sigla_tipo", "numero", "ano", "impacto_fiscal")
    list_filter = ("casa", "impacto_fiscal")
    search_fields = ("identifier", "sigla_tipo", "numero", "ano", "ementa")
    ordering = ("casa", "sigla_tipo", "numero", "ano")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("external_id", "proposition", "casa", "data_evento", "colegiado")
    list_filter = ("casa", "plenario_ou_comissao")
    search_fields = ("external_id", "colegiado", "proposition__identifier")
    ordering = ("-data_evento",)


@admin.register(MonitoredProposition)
class MonitoredPropositionAdmin(admin.ModelAdmin):
    list_display = ("proposition", "prioridade", "destaque", "selecionado_por", "selecionado_em")
    list_filter = ("destaque", "prioridade")
    search_fields = ("proposition__identifier", "proposition__ementa")
    ordering = ("-destaque", "-prioridade")


@admin.register(Tramitacao)
class TramitacaoAdmin(admin.ModelAdmin):
    list_display = ("monitored", "data", "origem")
    list_filter = ("origem",)
    search_fields = ("monitored__proposition__identifier", "descricao")
    ordering = ("-data",)
