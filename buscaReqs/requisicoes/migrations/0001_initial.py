from __future__ import annotations

from django.db import migrations, models


DEFAULT_PROPOSITION_TYPES = [
    "RIC",
    "INC",
    "REQ",
    "RCP",
    "REL",
    "RDP",
    "REC",
    "RQN",
    "RPD",
    "RQC",
    "RCM",
]

DEFAULT_PRESENTATION_YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]

DEFAULT_SUBJECTS = [
    {"value": "estatais", "label": "Estatais"},
    {"value": "L14133", "label": "Lei nº 14.133/2021"},
    {"value": "L8112", "label": "Lei nº 8.112/1990"},
    {"value": "LGPD", "label": "LGPD"},
    {"value": "LAI", "label": "LAI"},
    {"value": "D11345", "label": "Decreto nº 11.345/2023"},
    {"value": "PPA", "label": "PPA"},
]


def bootstrap_configuration(apps, schema_editor) -> None:  # pragma: no cover
    configuration_model = apps.get_model("requisicoes", "Configuration")
    configuration_model.objects.update_or_create(
        name="default",
        defaults={
            "proposition_types": DEFAULT_PROPOSITION_TYPES,
            "presentation_years": DEFAULT_PRESENTATION_YEARS,
            "subjects": DEFAULT_SUBJECTS,
        },
    )


def noop(apps, schema_editor) -> None:  # pragma: no cover
    pass


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Configuration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="default", max_length=64, unique=True)),
                ("proposition_types", models.JSONField(blank=True, default=list)),
                ("presentation_years", models.JSONField(blank=True, default=list)),
                ("subjects", models.JSONField(blank=True, default=list)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.RunPython(bootstrap_configuration, noop),
    ]
