from __future__ import annotations

import csv
import io
from django.contrib import messages
from django.forms import modelformset_factory
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import AddMonitorForm, BulkUploadForm, MonitorSelectionForm
from .models import Event, MonitoredProposition, Proposition

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


def index(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    can_configure = profile in ALLOWED_CONFIG_PROFILES

    total_proposicoes = Proposition.objects.count()
    total_monitoradas = MonitoredProposition.objects.count()

    proximos_eventos = (
        Event.objects.order_by("data_evento", "hora_evento")
        .filter(data_evento__gte=timezone.localdate())[:20]
    )

    recentes = MonitoredProposition.objects.select_related("proposition").order_by("-selecionado_em")[:20]

    context = {
        "profile": profile,
        "can_configure": can_configure,
        "total_proposicoes": total_proposicoes,
        "total_monitoradas": total_monitoradas,
        "proximos_eventos": proximos_eventos,
        "recentes": recentes,
        "manage_url": _append_profile(_prefixed_path(request, reverse("agenda:manage")), profile) if can_configure else "",
    }
    return render(request, "agenda/index.html", context)


def manage(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    if profile not in ALLOWED_CONFIG_PROFILES:
        messages.error(request, "Somente perfis administrador ou operador podem gerenciar monitoramentos.")
        return redirect(_append_profile(_prefixed_path(request, reverse("agenda:index")), profile))

    MonitorFormSet = modelformset_factory(
        MonitoredProposition,
        form=MonitorSelectionForm,
        extra=0,
        can_delete=True,
    )

    queryset = MonitoredProposition.objects.select_related("proposition").order_by("-destaque", "-prioridade", "proposition__identifier")

    formset = MonitorFormSet(queryset=queryset, prefix="monitor")
    available_props = Proposition.objects.exclude(monitoramento__isnull=False).order_by("casa", "identifier")
    add_form = AddMonitorForm(queryset=available_props)
    upload_form = BulkUploadForm()

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "update":
            formset = MonitorFormSet(request.POST, queryset=queryset, prefix="monitor")
            if formset.is_valid():
                _save_formset(formset, selecionado_por=profile)
                messages.success(request, "Monitoramentos atualizados.")
                return redirect(_append_profile(_prefixed_path(request, reverse("agenda:manage")), profile))
            messages.error(request, "Corrija os erros e tente novamente.")
        elif action == "add":
            add_form = AddMonitorForm(request.POST, queryset=available_props)
            if add_form.is_valid():
                proposition = add_form.cleaned_data["proposition"]
                MonitoredProposition.objects.update_or_create(
                    proposition=proposition,
                    defaults={"selecionado_por": profile},
                )
                messages.success(request, f"Proposição {proposition.identifier} adicionada à lista de monitoramento.")
                return redirect(_append_profile(_prefixed_path(request, reverse("agenda:manage")), profile))
            messages.error(request, "Selecione uma proposição válida.")
        elif action == "upload":
            upload_form = BulkUploadForm(request.POST, request.FILES)
            if upload_form.is_valid():
                arquivo = upload_form.cleaned_data["arquivo"]
                _process_csv_upload(arquivo, profile)
                messages.success(request, "Arquivo processado. Monitoramentos atualizados.")
                return redirect(_append_profile(_prefixed_path(request, reverse("agenda:manage")), profile))
            messages.error(request, "Falha ao processar o arquivo enviado.")
        else:
            messages.error(request, "Ação não reconhecida.")

    context = {
        "profile": profile,
        "formset": formset,
        "add_form": add_form,
        "upload_form": upload_form,
        "available_total": available_props.count(),
        "index_url": _append_profile(_prefixed_path(request, reverse("agenda:index")), profile),
    }
    return render(request, "agenda/manage.html", context)


def _save_formset(formset, selecionado_por: str) -> None:
    objetos = formset.save(commit=False)
    ids_salvos: list[int] = []
    for obj in objetos:
        obj.selecionado_por = obj.selecionado_por or selecionado_por
        obj.save()
        ids_salvos.append(obj.pk)
    for deletado in formset.deleted_objects:
        deletado.delete()


def _process_csv_upload(arquivo, selecionado_por: str) -> None:
    raw = arquivo.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    buffer = io.StringIO(text)
    reader = csv.DictReader(buffer)
    for row in reader:
        identifier = (row.get("identifier") or "").strip()
        if not identifier:
            continue
        try:
            proposition = Proposition.objects.get(identifier=identifier)
        except Proposition.DoesNotExist:
            continue
        prioridade = row.get("prioridade") or "0"
        destaque = str(row.get("destaque") or "").lower() in {"1", "true", "sim", "yes"}
        observacoes = row.get("observacoes") or ""
        MonitoredProposition.objects.update_or_create(
            proposition=proposition,
            defaults={
                "prioridade": int(prioridade) if prioridade.isdigit() else 0,
                "destaque": destaque,
                "observacoes": observacoes,
                "selecionado_por": selecionado_por,
            },
        )
