from django.db import models


class WeightNamespace(models.TextChoices):
    PESOS = "PESOS", "Pesos"
    PESOS_SMA = "PESOS_SMA", "Pesos SMA"


class WeightEntry(models.Model):
    namespace = models.CharField(
        max_length=32,
        choices=WeightNamespace.choices,
    )
    term = models.CharField(max_length=255)
    weight = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["namespace", "term"], name="unique_namespace_term"),
        ]
        ordering = ["term"]

    def __str__(self) -> str:
        return f"{self.namespace}::{self.term} ({self.weight})"
