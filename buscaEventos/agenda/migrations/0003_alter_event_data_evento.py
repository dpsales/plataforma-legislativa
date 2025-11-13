from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agenda", "0002_alter_proposition_justificativa"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="data_evento",
            field=models.DateField(blank=True, null=True),
        ),
    ]
