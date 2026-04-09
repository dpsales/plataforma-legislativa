from django.contrib import admin
from .models import EventoLegislativo, AtualizacaoProposicao, AgendaFavorita


@admin.register(EventoLegislativo)
class EventoLegislativoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'casa', 'data_evento', 'tipo', 'atualizado_em']
    list_filter = ['casa', 'tipo', 'data_evento']
    search_fields = ['titulo', 'descricao', 'codigo_evento']
    readonly_fields = ['codigo_evento', 'importado_em', 'atualizado_em']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo_evento', 'casa', 'titulo')
        }),
        ('Informações', {
            'fields': ('descricao', 'tipo', 'local', 'comissao')
        }),
        ('Data/Hora', {
            'fields': ('data_evento', 'hora_inicio', 'hora_fim')
        }),
        ('Links', {
            'fields': ('url_evento', 'url_transmissao')
        }),
        ('Rastreamento', {
            'fields': ('importado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AtualizacaoProposicao)
class AtualizacaoProposicaoAdmin(admin.ModelAdmin):
    list_display = ['codigo_material', 'tipo', 'data_atualizacao', 'origem']
    list_filter = ['tipo', 'origem', 'data_atualizacao']
    search_fields = ['codigo_material', 'descricao']
    readonly_fields = ['detectado_em']
    
    fieldsets = (
        ('Proposição', {
            'fields': ('codigo_material', 'casa')
        }),
        ('Atualização', {
            'fields': ('tipo', 'descricao', 'situacao_anterior', 'situacao_atual')
        }),
        ('Data/Origem', {
            'fields': ('data_atualizacao', 'origem', 'detectado_em')
        }),
    )


@admin.register(AgendaFavorita)
class AgendaFavoritaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'nome', 'criado_em']
    list_filter = ['tipo', 'criado_em', 'usuario']
    search_fields = ['nome', 'usuario__username']
    readonly_fields = ['criado_em']
