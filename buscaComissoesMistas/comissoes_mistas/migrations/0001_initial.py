from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Proposition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("proposition_id", models.CharField(max_length=64, unique=True)),
                ("sigla_tipo", models.CharField(blank=True, max_length=16)),
                ("numero", models.CharField(blank=True, max_length=16)),
                ("ano", models.CharField(blank=True, max_length=8)),
                ("proposicao", models.CharField(blank=True, max_length=64)),
                ("autor", models.CharField(blank=True, max_length=255)),
                ("ementa", models.TextField(blank=True)),
                ("situacao_sigla", models.CharField(blank=True, max_length=64)),
                ("situacao", models.CharField(blank=True, max_length=255)),
                ("comissao", models.CharField(blank=True, max_length=128)),
                ("data_situacao_recente", models.DateTimeField(blank=True, null=True)),
                ("historico", models.TextField(blank=True)),
                ("textos_associados", models.JSONField(blank=True, default=list)),
                ("ficha_tramitacao_url", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-data_situacao_recente", "-updated_at"],
            },
        ),
        migrations.RunSQL("DROP INDEX IF EXISTS comissoes_p_propos_6c0b9f_idx"),
        migrations.AddIndex(
            model_name="proposition",
            index=models.Index(fields=["proposition_id"], name="comissoes_p_propos_6c0b9f_idx"),
        ),
        migrations.RunSQL("DROP INDEX IF EXISTS comissoes_p_sigla_t_77b6ea_idx"),
        migrations.AddIndex(
            model_name="proposition",
            index=models.Index(fields=["sigla_tipo"], name="comissoes_p_sigla_t_77b6ea_idx"),
        ),
        migrations.RunSQL("DROP INDEX IF EXISTS comissoes_p_comis_814df4_idx"),
        migrations.AddIndex(
            model_name="proposition",
            index=models.Index(fields=["comissao"], name="comissoes_p_comis_814df4_idx"),
        ),
        migrations.RunSQL("DROP INDEX IF EXISTS comissoes_p_situac_5241b4_idx"),
        migrations.AddIndex(
            model_name="proposition",
            index=models.Index(fields=["situacao"], name="comissoes_p_situac_5241b4_idx"),
        ),
    ]
