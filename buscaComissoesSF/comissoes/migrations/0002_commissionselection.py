from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comissoes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommissionSelection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="default", max_length=64, unique=True)),
                ("siglas", models.JSONField(blank=True, default=list)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Seleção de comissões",
                "verbose_name_plural": "Seleções de comissões",
            },
        ),
    ]
