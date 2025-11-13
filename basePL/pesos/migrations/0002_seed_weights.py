from django.db import migrations

PESOS_ITEMS = [
    ("Gest\u00e3o", 14),
    ("Inova\u00e7\u00e3o", 14),
    ("Servi\u00e7os P\u00fablicos", 14),
    ("Administra\u00e7\u00e3o P\u00fablica Federal", 12),
    ("Governan\u00e7a", 10),
    ("Transforma\u00e7\u00e3o do Estado", 12),
    ("Moderniza\u00e7\u00e3o", 10),
    ("Governo Digital", 14),
    ("Digitaliza\u00e7\u00e3o", 12),
    ("Servi\u00e7os Digitais", 12),
    ("Carteira de Identidade Nacional", 14),
    ("CIN", 12),
    ("Identifica\u00e7\u00e3o Civil", 10),
    ("Infraestrutura Nacional de Dados", 10),
    ("IND", 8),
    ("Dados Abertos", 8),
    ("LGPD", 10),
    ("Privacidade", 10),
    ("Seguran\u00e7a da Informa\u00e7\u00e3o", 10),
    ("Intelig\u00eancia Artificial", 10),
    ("TIC", 8),
    ("Tecnologia da Informa\u00e7\u00e3o", 8),
    ("SEI", 8),
    ("Sistema Eletr\u00f4nico de Informa\u00e7\u00f5es", 8),
    ("Estrat\u00e9gia Federal de Governo Digital", 10),
    ("Cidadania Digital", 8),
    ("Servidor P\u00fablico", 14),
    ("Carreiras Transversais", 14),
    ("Carreira", 12),
    ("Cargos Efetivos", 12),
    ("Cargos em Comiss\u00e3o", 10),
    ("Fun\u00e7\u00f5es de Confian\u00e7a", 10),
    ("Remunera\u00e7\u00e3o", 10),
    ("Estrutura Remunerat\u00f3ria", 10),
    ("Vencimento B\u00e1sico", 8),
    ("Gratifica\u00e7\u00f5es", 8),
    ("Subs\u00eddio", 8),
    ("Reestrutura\u00e7\u00e3o de Carreiras", 12),
    ("Concurso P\u00fablico Nacional Unificado", 14),
    ("CNU", 12),
    ("Concursos P\u00fablicos", 12),
    ("Lei 8.112", 10),
    ("Estatuto do Servidor", 8),
    ("Sigepe", 8),
    ("Gest\u00e3o de Pessoas", 12),
    ("Desenvolvimento de Pessoas", 10),
    ("Rela\u00e7\u00f5es do Trabalho", 10),
    ("Negocia\u00e7\u00e3o Sindical", 8),
    ("Acumula\u00e7\u00e3o de Cargos", 8),
    ("Agentes P\u00fablicos", 10),
    ("Patrim\u00f4nio da Uni\u00e3o", 12),
    ("SPU", 8),
    ("Im\u00f3veis Funcionais", 6),
    ("Empresas Estatais", 10),
    ("Governan\u00e7a Corporativa", 8),
    ("SEST", 6),
    ("Compras P\u00fablicas Centralizadas", 12),
    ("Contrata\u00e7\u00f5es P\u00fablicas", 10),
    ("Log\u00edstica", 8),
    ("Enap", 8),
    ("Capacita\u00e7\u00e3o", 8),
    ("Funpresp-Exe", 6),
    ("Protocolo de Inten\u00e7\u00f5es", 6),
    ("Conv\u00eanios", 6),
    ("Transfer\u00eancias da Uni\u00e3o", 6),
    ("Atos Normativos", 6),
    ("Decretos", 6),
]

PESOS_SMA_ITEMS = [
    ("CMAP", 12),
    ("Conselho de Monitoramento e Avalia\u00e7\u00e3o de Pol\u00edticas P\u00fablicas", 12),
    ("Revis\u00e3o do Gasto", 10),
    ("Monitoramento e avalia\u00e7\u00e3o", 10),
    ("Monitoramento", 8),
    ("Avalia\u00e7\u00e3o", 8),
    ("Monitorar", 4),
    ("Avaliar", 4),
    ("Estudo de monitoramento", 8),
    ("Estudo de avalia\u00e7\u00e3o", 8),
    ("Relat\u00f3rio de monitoramento", 8),
    ("Relat\u00f3rio de avalia\u00e7\u00e3o", 8),
    ("Demonstrativos", 6),
    ("Subs\u00eddios", 10),
    ("Benef\u00edcios tribut\u00e1rios", 9),
    ("Benef\u00edcios financeiros", 9),
    ("Benef\u00edcios credit\u00edcios", 9),
    ("Gasto Direto", 5),
    ("Monitoramento econ\u00f4mico", 7),
    ("Monitoramento cont\u00e1bil", 7),
    ("Monitoramento financeiro", 7),
]


def seed_weights(apps, schema_editor):
    WeightEntry = apps.get_model("pesos", "WeightEntry")
    registros = []
    for term, weight in PESOS_ITEMS:
        registros.append(
            WeightEntry(namespace="PESOS", term=term, weight=weight)
        )
    for term, weight in PESOS_SMA_ITEMS:
        registros.append(
            WeightEntry(namespace="PESOS_SMA", term=term, weight=weight)
        )
    WeightEntry.objects.bulk_create(registros, ignore_conflicts=True)


def unseed_weights(apps, schema_editor):
    WeightEntry = apps.get_model("pesos", "WeightEntry")
    WeightEntry.objects.filter(namespace__in=["PESOS", "PESOS_SMA"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pesos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_weights, reverse_code=unseed_weights),
    ]
