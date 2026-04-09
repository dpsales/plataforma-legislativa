from django.contrib import admin

from .models import Configuration, Requerimento


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
	list_display = ("name", "updated_at")
	readonly_fields = ("updated_at",)
	search_fields = ("name",)


@admin.register(Requerimento)
class RequerimentoAdmin(admin.ModelAdmin):
	list_display = ("codigo_material", "titulo", "casa", "situacao", "data_ultima_tramitacao", "data_atualizacao")
	list_filter = ("casa", "situacao", "data_apresentacao", "data_atualizacao")
	search_fields = ("codigo_material", "titulo", "autor", "ementa")
	readonly_fields = ("codigo_material", "data_insercao", "data_atualizacao")
	fieldsets = (
		("Identificação", {
			"fields": ("codigo_material", "titulo", "casa")
		}),
		("Conteúdo", {
			"fields": ("ementa", "autor")
		}),
		("Situação e Tramitação", {
			"fields": ("situacao", "data_apresentacao", "data_ultima_tramitacao", "descricao_ultima_tramitacao")
		}),
		("Classificação", {
			"fields": ("termos_encontrados", "grupos_encontrados", "assuntos_encontrados", "local")
		}),
		("Links", {
			"fields": ("link_ficha", "link_inteiro_teor")
		}),
		("Auditoria", {
			"fields": ("data_insercao", "data_atualizacao"),
			"classes": ("collapse",)
		}),
	)
	ordering = ("-data_ultima_tramitacao", "-data_apresentacao")

