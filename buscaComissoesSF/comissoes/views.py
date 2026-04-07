from __future__ import annotations

from datetime import datetime
from typing import Iterable

import io
import pandas as pd
from django import forms
from django.contrib import messages
from django.db.models import Max, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import CommissionSelection, Proposition
from .services import fetch_commission_catalog


def _parse_multi(request: HttpRequest, key: str) -> list[str]:
    value = request.GET.get(key, "")
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


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


def _append_profile(path: str, profile: str) -> str:
    if not profile:
        return path
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}profile={profile}"


def _catalog_entries(catalogo: dict[str, object], extras: Iterable[str] | None = None) -> list[dict[str, str]]:
    catalog_senate = catalogo.get("senate", []) or []
    catalog_mixed = catalogo.get("mixed", []) or []
    seen: set[str] = set()
    entries: list[dict[str, str]] = []

    def _append(sigla: str | None, nome: str | None, origem: str) -> None:
        if not sigla:
            return
        sigla_norm = sigla.strip().upper()
        if not sigla_norm or sigla_norm in seen:
            return
        seen.add(sigla_norm)
        entries.append(
            {
                "sigla": sigla_norm,
                "nome": (nome or "").strip(),
                "origem": origem,
            }
        )

    for entry in catalog_senate:
        _append(entry.get("sigla"), entry.get("nome"), "senado")

    for entry in catalog_mixed:
        _append(entry.get("sigla"), entry.get("nome"), "mista")

    for value in extras or []:
        if value:
            _append(value, value, "dataset")

    if "PLEN" not in seen:
        entries.append({"sigla": "PLEN", "nome": "Plenário", "origem": "especial"})
        seen.add("PLEN")

    entries.sort(key=lambda item: item["sigla"])
    return entries


def _selected_commission_siglas() -> list[str]:
    selection = CommissionSelection.objects.filter(name=CommissionSelection.DEFAULT_NAME).first()
    if not selection or not selection.siglas:
        return []
    return [sigla.strip().upper() for sigla in selection.siglas if sigla]


def index(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    can_configure = profile in ALLOWED_CONFIG_PROFILES

    tipos = Proposition.objects.order_by().values_list("sigla_tipo", flat=True).distinct()
    comissoes = Proposition.objects.order_by().values_list("comissao", flat=True).distinct()
    situacoes = Proposition.objects.order_by().values_list("situacao", flat=True).distinct()
    last_update = Proposition.objects.aggregate(last=Max("updated_at"))["last"] or timezone.now()
    catalogo = fetch_commission_catalog()
    selected_siglas = _selected_commission_siglas()
    all_commissions = _catalog_entries(catalogo, comissoes)

    generated_at = catalogo.get("generated_at")
    if isinstance(generated_at, datetime):
        generated_at = timezone.localtime(generated_at)

    api_url = _append_profile(_prefixed_path(request, reverse("comissoes:propositions-api")), profile)
    export_url = _append_profile(_prefixed_path(request, reverse("comissoes:export-xlsx")), profile)
    configure_url = ""
    if can_configure:
        configure_path = _prefixed_path(request, reverse("comissoes:configure"))
        configure_url = _append_profile(configure_path, profile)

    context = {
        "types": [value for value in tipos if value],
        "comissoes": [value for value in comissoes if value],
        "situacoes": [value for value in situacoes if value],
        "all_commissions": all_commissions,
        "selected_commissions": selected_siglas,
        "last_update": timezone.localtime(last_update),
        "selection_configured": bool(selected_siglas),
        "api_url": api_url,
        "export_url": export_url,
        "static_prefix": _prefixed_path(request, "static").rstrip("/"),
        "configure_url": configure_url,
        "catalog_senate": catalogo.get("senate", []) or [],
        "catalog_mixed": catalogo.get("mixed", []) or [],
        "catalog_generated_at": generated_at,
        "can_configure": can_configure,
        "profile": profile,
    }
    return render(request, "comissoes/index.html", context)


class CommissionSelectionForm(forms.Form):
    commissions = forms.MultipleChoiceField(
        label="Comissões monitoradas",
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 25}),
    )

    def __init__(self, *args, choices: Iterable[tuple[str, str]] | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["commissions"].choices = list(choices or [])


def configure_commissions(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    if profile not in ALLOWED_CONFIG_PROFILES:
        messages.error(request, "Somente perfis administrador ou normal podem configurar as comissões monitoradas.")
        index_path = _append_profile(_prefixed_path(request, reverse("comissoes:index")), profile)
        return redirect(index_path)

    catalogo = fetch_commission_catalog()
    selected_siglas = _selected_commission_siglas()

    entries = _catalog_entries(catalogo)
    choices = [
        (
            item["sigla"],
            (
                f"{item['sigla']} — {item['nome']}" if item["nome"] else item["sigla"]
            )
            + (" (Comissão Mista)" if item["origem"] == "mista" else ""),
        )
        for item in entries
    ]

    if request.method == "POST":
        form = CommissionSelectionForm(request.POST, choices=choices)
        if form.is_valid():
            siglas = [sigla.strip().upper() for sigla in form.cleaned_data["commissions"] if sigla]
            objeto, _ = CommissionSelection.objects.get_or_create(name=CommissionSelection.DEFAULT_NAME)
            objeto.siglas = siglas
            objeto.save()
            messages.success(request, "Seleção de comissões atualizada com sucesso.")
            configure_path = _append_profile(_prefixed_path(request, reverse("comissoes:configure")), profile)
            return redirect(configure_path)
    else:
        form = CommissionSelectionForm(initial={"commissions": selected_siglas}, choices=choices)

    generated_at = catalogo.get("generated_at")
    if isinstance(generated_at, datetime):
        generated_at = timezone.localtime(generated_at)

    context = {
        "form": form,
        "selected_count": len(selected_siglas),
        "catalog_generated_at": generated_at,
        "all_commissions": entries,
        "selected_commissions": selected_siglas,
        "index_url": _append_profile(_prefixed_path(request, reverse("comissoes:index")), profile),
        "profile": profile,
    }
    return render(request, "comissoes/manage_commissions.html", context)


def _apply_filters(
    queryset,
    tipos: Iterable[str],
    comissoes: Iterable[str],
    situacoes: Iterable[str],
    busca: str,
):
    if tipos:
        queryset = queryset.filter(sigla_tipo__in=list(tipos))
    if comissoes:
        queryset = queryset.filter(comissao__in=list(comissoes))
    if situacoes:
        queryset = queryset.filter(situacao__in=list(situacoes))
    if busca:
        queryset = queryset.filter(
            Q(ementa__icontains=busca)
            | Q(autor__icontains=busca)
            | Q(proposicao__icontains=busca)
        )
    return queryset


def propositions_api(request: HttpRequest) -> JsonResponse:
    tipos = _parse_multi(request, "tipos")
    comissoes = _parse_multi(request, "comissoes")
    situacoes = _parse_multi(request, "situacoes")
    busca = request.GET.get("busca", "").strip()

    queryset = Proposition.objects.all()
    queryset = _apply_filters(queryset, tipos, comissoes, situacoes, busca)
    selecionadas = _selected_commission_siglas()
    if selecionadas:
        queryset = queryset.filter(comissao__in=list(selecionadas))

    dados = []
    for prop in queryset.order_by("-data_situacao_recente", "-updated_at"):
        data_ultima = (
            timezone.localtime(prop.data_situacao_recente).strftime("%d/%m/%Y %H:%M")
            if prop.data_situacao_recente
            else ""
        )
        dados.append(
            {
                "proposicao": prop.proposicao,
                "sigla_tipo": prop.sigla_tipo,
                "autor": prop.autor,
                "ementa": prop.ementa,
                "situacao": prop.situacao,
                "comissao": prop.comissao,
                "data_ultima_tramitacao": data_ultima,
                "historico": prop.historico,
                "textos_associados": prop.textos_associados,
                "ficha_url": prop.ficha_tramitacao_url,
            }
        )

    return JsonResponse({"results": dados})


def export_xlsx(request: HttpRequest) -> HttpResponse:
    tipos = _parse_multi(request, "tipos")
    comissoes = _parse_multi(request, "comissoes")
    situacoes = _parse_multi(request, "situacoes")
    queryset = Proposition.objects.all()
    queryset = _apply_filters(queryset, tipos, comissoes, situacoes, request.GET.get("busca", "").strip())
    selecionadas = _selected_commission_siglas()
    if selecionadas:
        queryset = queryset.filter(comissao__in=list(selecionadas))

    data = []
    for prop in queryset.order_by("-data_situacao_recente"):
        textos = prop.textos_associados or []
        textos_str = "\n".join(f"{item.get('label')}: {item.get('url')}" for item in textos if item)
        data.append(
            {
                "Proposição": prop.proposicao,
                "Autor": prop.autor,
                "Ementa": prop.ementa,
                "Situação": prop.situacao,
                "Comissão": prop.comissao,
                "Data último status": (
                    timezone.localtime(prop.data_situacao_recente).strftime("%d/%m/%Y %H:%M")
                    if prop.data_situacao_recente
                    else ""
                ),
                "Textos associados": textos_str,
                "Ficha de tramitação": prop.ficha_tramitacao_url,
            }
        )

    df = pd.DataFrame(data)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)

    filename = timezone.now().strftime("proposicoes_comissoes_sf_%Y%m%d_%H%M%S.xlsx")
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
