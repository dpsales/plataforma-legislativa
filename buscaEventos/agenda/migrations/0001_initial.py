from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Proposition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("identifier", models.CharField(max_length=128, unique=True)),
                ("casa", models.CharField(choices=[("CD", "Câmara dos Deputados"), ("SF", "Senado Federal")], max_length=2)),
                ("sigla_tipo", models.CharField(blank=True, max_length=16)),
                ("numero", models.CharField(blank=True, max_length=16)),
                ("ano", models.CharField(blank=True, max_length=8)),
                ("ementa", models.TextField(blank=True)),
                ("justificativa", models.TextField(blank=True)),
                ("autor", models.CharField(blank=True, max_length=255)),
                ("autor_partido_uf", models.CharField(blank=True, max_length=255)),
                ("link_inteiro_teor", models.URLField(blank=True)),
                ("link_ficha", models.URLField(blank=True)),
                ("tem_pl", models.BooleanField(default=False)),
                ("impacto_fiscal", models.CharField(blank=True, max_length=255)),
                ("impacto_categoria", models.CharField(blank=True, max_length=255)),
                ("palavras_chave", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["casa", "sigla_tipo", "numero", "ano"],
            },
        ),
        migrations.CreateModel(
            name="MonitoredProposition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prioridade", models.PositiveIntegerField(default=0)),
                ("destaque", models.BooleanField(default=False)),
                ("observacoes", models.TextField(blank=True)),
                ("selecionado_por", models.CharField(blank=True, max_length=64)),
                ("selecionado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "proposition",
                    models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="monitoramento", to="agenda.proposition"),
                ),
            ],
            options={
                "ordering": ["-destaque", "-prioridade", "proposition__identifier"],
            },
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.CharField(max_length=128)),
                ("casa", models.CharField(choices=[("CD", "Câmara dos Deputados"), ("SF", "Senado Federal")], max_length=2)),
                ("colegiado", models.CharField(max_length=255)),
                ("data_evento", models.DateField()),
                ("hora_evento", models.CharField(blank=True, max_length=16)),
                ("link_colegiado", models.URLField(blank=True)),
                ("plenario_ou_comissao", models.CharField(blank=True, max_length=64)),
                ("marcar_para_relatorio", models.BooleanField(default=False)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "proposition",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="events", to="agenda.proposition"),
                ),
            ],
            options={
                "ordering": ["-data_evento", "-criado_em"],
                "unique_together": {("external_id", "proposition")},
            },
        ),
        migrations.CreateModel(
            name="Tramitacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("data", models.DateTimeField()),
                ("descricao", models.TextField()),
                ("origem", models.CharField(blank=True, max_length=255)),
                ("link", models.URLField(blank=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "monitored",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="tramitacoes", to="agenda.monitoredproposition"),
                ),
            ],
            options={
                "ordering": ["-data", "-criado_em"],
            },
        ),
    ]
