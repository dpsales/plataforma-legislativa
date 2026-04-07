from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agenda", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="proposition",
            name="justificativa",
            field=models.TextField(blank=True, default=""),
        ),
    ]
