from __future__ import annotations

from django.db import migrations, models

DEFAULT_UNIT_GROUPS = [
    {
        "value": "gabinete-ministra",
        "label": "Gabinete da Ministra",
        "terms": [
            "Esther Dweck",
            "Ministério da Gestão",
            "Ministério da Gestão e da Inovação em Serviços Públicos",
            "Ministra da Gestão",
            "Ministra de Estado da Gestão e da Inovação em Serviços Públicos",
            "Transformação do Estado",
            "Reforma Administrativa",
        ],
    },
    {
        "value": "gestao-pessoas",
        "label": "Gestão de Pessoas e Relações do Trabalho",
        "terms": [
            "Secretaria de Gestão de Pessoas",
            "SGP",
            "Secretaria de Relações do Trabalho",
            "SRT",
            "Concurso Público Nacional Unificado",
            "CNU",
            "Carreiras Transversais",
            "Remuneração",
            "eSocial",
            "Sigepe",
            "Lei 8.112",
        ],
    },
    {
        "value": "governo-digital",
        "label": "Secretaria de Governo Digital",
        "terms": [
            "Secretaria de Governo Digital",
            "SGD",
            "Carteira de Identidade Nacional",
            "CIN",
            "Gov.br",
            "Serviços Digitais",
            "Inovação Governamental",
            "Segurança da Informação",
            "LGPD",
            "SISP",
        ],
    },
    {
        "value": "logistica-seges",
        "label": "Gestão e Inovação / Logística",
        "terms": [
            "Secretaria de Gestão e Inovação",
            "SEGES",
            "Central de Compras",
            "Contratações Públicas",
            "Nova Lei de Licitações",
            "Lei nº 14.133",
            "Logística",
            "Modelos Organizacionais",
            "Sustentabilidade",
        ],
    },
    {
        "value": "patrimonio-spu",
        "label": "Secretaria do Patrimônio da União",
        "terms": [
            "Secretaria do Patrimônio da União",
            "SPU",
            "Imóveis da União",
            "Destinação de Imóveis",
            "Receitas Patrimoniais",
        ],
    },
    {
        "value": "sest-estatais",
        "label": "Secretaria de Coordenação e Governança das Estatais",
        "terms": [
            "Secretaria de Coordenação e Governança das Empresas Estatais",
            "SEST",
            "Empresas Estatais",
            "Governança Corporativa",
            "IG-Sest",
        ],
    },
    {
        "value": "entidades-vinculadas",
        "label": "Entidades Vinculadas e Conselhos",
        "terms": [
            "Dataprev",
            "Enap",
            "Fundação Escola Nacional de Administração Pública",
            "Funpresp-Exe",
            "CMAP",
            "Conselho de Monitoramento e Avaliação de Políticas Públicas",
        ],
    },
]

DEFAULT_SUBJECTS = [
    {"value": "estatais", "label": "Estatais"},
    {"value": "L14133", "label": "Lei nº 14.133/2021"},
    {"value": "L8112", "label": "Lei nº 8.112/1990"},
    {"value": "LGPD", "label": "LGPD"},
    {"value": "LAI", "label": "LAI"},
    {"value": "D11345", "label": "Decreto nº 11.345/2023"},
    {"value": "PPA", "label": "PPA"},
]


def seed_unit_groups(apps, schema_editor) -> None:  # pragma: no cover
    configuration_model = apps.get_model("requisicoes", "Configuration")
    config, _ = configuration_model.objects.get_or_create(name="default")

    if not config.unit_groups:
        config.unit_groups = DEFAULT_UNIT_GROUPS
    if not config.subjects:
        config.subjects = DEFAULT_SUBJECTS
    else:
        normalised_subjects = []
        for item in config.subjects:
            value = str(item.get("value", "")).strip()
            label = item.get("label", "")
            if isinstance(label, (set, list, tuple)):
                continue
            label_str = str(label).strip()
            if not value:
                value = label_str.lower().replace(" ", "_") if label_str else "assunto"
            if not label_str:
                label_str = value
            normalised_subjects.append({"value": value, "label": label_str})
        config.subjects = normalised_subjects or DEFAULT_SUBJECTS
    config.save(update_fields=["unit_groups", "subjects", "updated_at"])


def drop_unit_groups(apps, schema_editor) -> None:  # pragma: no cover
    configuration_model = apps.get_model("requisicoes", "Configuration")
    configuration_model.objects.update(unit_groups=[])


class Migration(migrations.Migration):

    dependencies = [
        ("requisicoes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuration",
            name="unit_groups",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(seed_unit_groups, drop_unit_groups),
    ]
