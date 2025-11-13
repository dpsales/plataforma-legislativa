from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="WeightEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("namespace", models.CharField(choices=[("PESOS", "Pesos"), ("PESOS_SMA", "Pesos SMA")], max_length=32)),
                ("term", models.CharField(max_length=255)),
                ("weight", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["term"],
            },
        ),
        migrations.AddConstraint(
            model_name="weightentry",
            constraint=models.UniqueConstraint(fields=("namespace", "term"), name="unique_namespace_term"),
        ),
    ]
