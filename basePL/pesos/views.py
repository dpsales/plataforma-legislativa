from __future__ import annotations

from typing import Iterable

from django.contrib import messages
from django.forms import modelformset_factory
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import NewWeightEntryForm, WeightEntryForm
from .models import WeightEntry, WeightNamespace

ALLOWED_CONFIG_PROFILES = {"admin", "normal"}


def _request_profile(request: HttpRequest) -> str:
    for source in (request.GET, request.POST):
        profile = source.get("profile")
        if profile:
            return profile.strip().lower()
    header = request.META.get("HTTP_X_USER_PROFILE")
    if header:
        return header.strip().lower()
    return ""


def _prefixed_path(request: HttpRequest, path: str) -> str:
    prefix = request.META.get("HTTP_X_FORWARDED_PREFIX") or request.META.get("SCRIPT_NAME") or ""
    prefix = prefix.rstrip("/")
    if path.startswith("http://") or path.startswith("https://"):
        return path
    relative = path.lstrip("/")
    if prefix:
        base = prefix or "/"
        return f"{base}/{relative}" if relative else base
    return f"/{relative}" if relative else "/"


def _append_profile(path: str, profile: str) -> str:
    if not profile:
        return path
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}profile={profile}"


def _build_formset(queryset: Iterable[WeightEntry], prefix: str, data=None):
    FormSet = modelformset_factory(
        WeightEntry,
        form=WeightEntryForm,
        extra=0,
        can_delete=True,
    )
    return FormSet(data=data, queryset=queryset, prefix=prefix)


def index(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    can_configure = profile in ALLOWED_CONFIG_PROFILES

    pesos_qs = WeightEntry.objects.filter(namespace=WeightNamespace.PESOS).order_by("term")
    sma_qs = WeightEntry.objects.filter(namespace=WeightNamespace.PESOS_SMA).order_by("term")

    pesos_formset = _build_formset(pesos_qs, prefix="pesos")
    sma_formset = _build_formset(sma_qs, prefix="sma")
    new_entry_form = NewWeightEntryForm()

    if request.method == "POST":
        if not can_configure:
            messages.error(request, "Somente administradores ou operadores podem alterar os pesos.")
            return redirect(_append_profile(_prefixed_path(request, reverse("pesos:index")), profile))

        action = request.POST.get("action", "")
        if action == "update_pesos":
            pesos_formset = _build_formset(pesos_qs, prefix="pesos", data=request.POST)
            if pesos_formset.is_valid():
                _save_formset(pesos_formset, WeightNamespace.PESOS)
                messages.success(request, "Tabela de Pesos atualizada com sucesso.")
                return redirect(_append_profile(_prefixed_path(request, reverse("pesos:index")), profile))
            messages.error(request, "Corrija os erros na tabela de Pesos e tente novamente.")
        elif action == "update_pesos_sma":
            sma_formset = _build_formset(sma_qs, prefix="sma", data=request.POST)
            if sma_formset.is_valid():
                _save_formset(sma_formset, WeightNamespace.PESOS_SMA)
                messages.success(request, "Tabela de Pesos SMA atualizada com sucesso.")
                return redirect(_append_profile(_prefixed_path(request, reverse("pesos:index")), profile))
            messages.error(request, "Corrija os erros na tabela de Pesos SMA e tente novamente.")
        elif action == "add_entry":
            new_entry_form = NewWeightEntryForm(request.POST)
            if new_entry_form.is_valid():
                novo = new_entry_form.save(commit=False)
                novo.namespace = new_entry_form.cleaned_data["namespace"]
                try:
                    existing = WeightEntry.objects.get(namespace=novo.namespace, term=novo.term)
                except WeightEntry.DoesNotExist:
                    novo.save()
                    messages.success(request, "Novo termo adicionado.")
                else:
                    existing.weight = novo.weight
                    existing.save(update_fields=["weight", "updated_at"])
                    messages.info(request, "Termo existente atualizado com o novo peso.")
                return redirect(_append_profile(_prefixed_path(request, reverse("pesos:index")), profile))
            messages.error(request, "Corrija os erros do formulário e tente novamente.")
        else:
            messages.error(request, "Ação não reconhecida.")

    context = {
        "profile": profile,
        "can_configure": can_configure,
        "pesos_formset": pesos_formset,
        "sma_formset": sma_formset,
        "new_entry_form": new_entry_form,
        "pesos_entries": list(pesos_qs),
        "sma_entries": list(sma_qs),
        "static_prefix": _prefixed_path(request, "static").rstrip("/"),
    }
    return render(request, "pesos/manage_weights.html", context)


def _save_formset(formset, namespace: str) -> None:
    objetos = formset.save(commit=False)
    for obj in objetos:
        obj.namespace = namespace
        obj.save()
    for deletado in formset.deleted_objects:
        deletado.delete()
