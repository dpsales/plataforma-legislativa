from django.contrib import admin

from .models import Proposition


@admin.register(Proposition)
class PropositionAdmin(admin.ModelAdmin):
    list_display = ("proposicao", "sigla_tipo", "situacao", "orgao_sigla", "data_ultima_tramitacao")
    search_fields = ("proposicao", "autor", "ementa", "situacao")
    list_filter = ("sigla_tipo", "orgao_sigla", "situacao")
    ordering = ("-data_ultima_tramitacao",)
