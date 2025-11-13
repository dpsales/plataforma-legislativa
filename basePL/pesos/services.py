from __future__ import annotations

from typing import Dict

from .models import WeightEntry, WeightNamespace


def load_weights(namespace: str) -> Dict[str, int]:
    entries = WeightEntry.objects.filter(namespace=namespace).values_list("term", "weight")
    return {term: weight for term, weight in entries}


def load_all_weights() -> Dict[str, Dict[str, int]]:
    return {
        WeightNamespace.PESOS: load_weights(WeightNamespace.PESOS),
        WeightNamespace.PESOS_SMA: load_weights(WeightNamespace.PESOS_SMA),
    }
