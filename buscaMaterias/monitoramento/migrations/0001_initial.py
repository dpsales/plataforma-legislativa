from __future__ import annotations

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TrackedDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(default="default", max_length=64, unique=True)),
                ("name", models.CharField(default="Documento de acompanhamento", max_length=120)),
                ("description", models.TextField(blank=True)),
                ("reference_label", models.CharField(blank=True, max_length=120)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("last_updated_profile", models.CharField(blank=True, max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Documento monitorado",
                "verbose_name_plural": "Documentos monitorados",
            },
        ),
        migrations.CreateModel(
            name="TrackedProposition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("proposition_id", models.BigIntegerField()),
                (
                    "casa",
                    models.CharField(
                        choices=[("camara", "Câmara"), ("senado", "Senado")],
                        max_length=16,
                    ),
                ),
                ("secretaria", models.CharField(blank=True, max_length=120)),
                ("tipo_sigla", models.CharField(blank=True, max_length=20)),
                ("numero", models.CharField(blank=True, max_length=20)),
                ("ano", models.PositiveIntegerField(blank=True, null=True)),
                ("assunto", models.CharField(blank=True, max_length=255)),
                ("prioridade", models.IntegerField(blank=True, null=True)),
                ("justificativa", models.TextField(blank=True)),
                ("titulo", models.CharField(blank=True, max_length=255)),
                ("ementa", models.TextField(blank=True)),
                ("autor", models.CharField(blank=True, max_length=255)),
                ("status", models.CharField(blank=True, max_length=255)),
                ("ultima_movimentacao", models.TextField(blank=True)),
                ("data_movimentacao", models.DateTimeField(blank=True, null=True)),
                ("link_ficha", models.URLField(blank=True)),
                ("link_inteiro_teor", models.URLField(blank=True)),
                ("fonte", models.CharField(blank=True, max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="propositions",
                        to="monitoramento.trackeddocument",
                    ),
                ),
            ],
            options={
                "ordering": ["-data_movimentacao", "-updated_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="trackedproposition",
            constraint=models.UniqueConstraint(fields=("document", "proposition_id"), name="uniq_document_proposition"),
        ),
        migrations.AddIndex(
            model_name="trackedproposition",
            index=models.Index(fields=["document", "casa"], name="monitoramento_doc_casa_idx"),
        ),
        migrations.AddIndex(
            model_name="trackedproposition",
            index=models.Index(fields=["document", "secretaria"], name="monitoramento_doc_secretaria_idx"),
        ),
        migrations.AddIndex(
            model_name="trackedproposition",
            index=models.Index(fields=["document", "prioridade"], name="monitoramento_doc_prioridade_idx"),
        ),
    ]
