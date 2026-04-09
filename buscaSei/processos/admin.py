from django.contrib import admin
from .models import ProcessoSEI, AndamentoProcesso, DocumentoProcesso


@admin.register(ProcessoSEI)
class ProcessoSEIAdmin(admin.ModelAdmin):
    list_display = ('numero_processo', 'assunto', 'status', 'data_consulta')
    list_filter = ('status', 'data_consulta')
    search_fields = ('numero_processo', 'assunto', 'interessado')
    readonly_fields = ('data_consulta', 'data_atualizacao')


@admin.register(AndamentoProcesso)
class AndamentoProcessoAdmin(admin.ModelAdmin):
    list_display = ('processo', 'data_andamento', 'tipo_movimentacao')
    list_filter = ('data_andamento', 'setor')
    search_fields = ('processo__numero_processo', 'tipo_movimentacao')
    readonly_fields = ('data_insercao',)


@admin.register(DocumentoProcesso)
class DocumentoProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero_documento', 'processo', 'tipo_documento', 'data_documento')
    list_filter = ('tipo_documento', 'data_documento')
    search_fields = ('processo__numero_processo', 'numero_documento', 'tipo_documento')
    readonly_fields = ('data_insercao',)
