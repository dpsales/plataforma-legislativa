from __future__ import annotations

from datetime import datetime
from typing import Iterable

import io
import pandas as pd
from django import forms
from django.contrib import messages
from django.db.models import Max
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import CommissionSelection, Proposition
from .services import fetch_orgao_catalog, selected_orgao_siglas


def _parse_multi(request: HttpRequest, key: str) -> list[str]:
    value = request.GET.get(key, "")
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _prefixed_path(request: HttpRequest, path: str) -> str:
    """Return a host-relative path honoring reverse proxy prefixes."""
    prefix = request.META.get("HTTP_X_FORWARDED_PREFIX") or request.META.get("SCRIPT_NAME") or ""
    prefix = prefix.rstrip("/")

    if path.startswith("http://") or path.startswith("https://"):
        return path

    relative = path.lstrip("/")
    if prefix:
        return f"{prefix}/{relative}" if relative else prefix or "/"
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


def index(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    can_configure = profile in ALLOWED_CONFIG_PROFILES

    types = Proposition.objects.order_by().values_list("sigla_tipo", flat=True).distinct()
    orgaos = Proposition.objects.order_by().values_list("orgao_sigla", flat=True).distinct()
    situacoes = Proposition.objects.order_by().values_list("situacao", flat=True).distinct()
    last_update = (
        Proposition.objects.aggregate(last=Max("updated_at"))["last"]
        or timezone.now()
    )

    catalogo = fetch_orgao_catalog()
    selection = CommissionSelection.objects.filter(name=CommissionSelection.DEFAULT_NAME).first()
    selected_siglas = [sigla.strip().upper() for sigla in (selection.siglas if selection and selection.siglas else []) if sigla]
    selection_configured = bool(selected_siglas)

    entries = catalogo.get("orgaos", []) or []
    entry_map: dict[str, dict[str, str]] = {}
    for item in entries:
        sigla = str(item.get("sigla", "")).strip().upper()
        if not sigla:
            continue
        entry_map[sigla] = {"sigla": sigla, "nome": str(item.get("nome", "")).strip()}

    for value in orgaos:
        if not value:
            continue
        sigla = value.strip().upper()
        entry_map.setdefault(sigla, {"sigla": sigla, "nome": sigla})

    all_orgaos = sorted(entry_map.values(), key=lambda item: item.get("sigla", ""))

    generated_at = catalogo.get("generated_at")
    if isinstance(generated_at, datetime):
        generated_at = timezone.localtime(generated_at)

    api_url = _append_profile(_prefixed_path(request, reverse("comissoes:propositions-api")), profile)
    export_url = _append_profile(_prefixed_path(request, reverse("comissoes:export-xlsx")), profile)
    configure_url = _append_profile(_prefixed_path(request, reverse("comissoes:configure")), profile) if can_configure else ""

    context = {
        "types": [t for t in types if t],
        "orgaos": [o for o in orgaos if o],
        "situacoes": [s for s in situacoes if s],
        "last_update": timezone.localtime(last_update),
        "api_url": api_url,
        "export_url": export_url,
        "static_prefix": _prefixed_path(request, "static").rstrip("/"),
        "all_orgaos": all_orgaos,
        "selected_orgaos": selected_siglas,
        "selection_configured": selection_configured,
        "can_configure": can_configure,
        "configure_url": configure_url,
        "profile": profile,
        "catalog_generated_at": generated_at,
    }
    return render(request, "comissoes/index.html", context)


class CommissionSelectionForm(forms.Form):
    organs = forms.MultipleChoiceField(
        label="Órgãos monitorados",
        required=False,
        widget=forms.SelectMultiple(attrs={
            "class": "form-select",
            "size": 25,
            "id": "id_organs",
        }),
    )

    def __init__(self, *args, choices: Iterable[tuple[str, str]] | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["organs"].choices = list(choices or [])


def configure_commissions(request: HttpRequest) -> HttpResponse:
    profile = _request_profile(request)
    if profile not in ALLOWED_CONFIG_PROFILES:
        messages.error(request, "Somente perfis administrador ou operador podem alterar a seleção de órgãos.")
        index_url = _append_profile(_prefixed_path(request, reverse("comissoes:index")), profile)
        return redirect(index_url)

    catalogo = fetch_orgao_catalog()
    selection = CommissionSelection.objects.filter(name=CommissionSelection.DEFAULT_NAME).first()
    selected_siglas = [sigla.strip().upper() for sigla in (selection.siglas if selection and selection.siglas else []) if sigla]

    entries = catalogo.get("orgaos", []) or []
    choices = [
        (
            item.get("sigla", "").strip().upper(),
            (
                f"{item.get('sigla', '').strip().upper()} — {item.get('nome', '').strip()}"
                if item.get("nome")
                else item.get("sigla", "").strip().upper()
            ),
        )
        for item in entries
        if item.get("sigla")
    ]

    if request.method == "POST":
        form = CommissionSelectionForm(request.POST, choices=choices)
        if form.is_valid():
            siglas = [sigla.strip().upper() for sigla in form.cleaned_data["organs"] if sigla]
            objeto, _ = CommissionSelection.objects.get_or_create(name=CommissionSelection.DEFAULT_NAME)
            objeto.siglas = siglas
            objeto.save()
            messages.success(request, "Seleção de órgãos atualizada com sucesso.")
            return redirect(_append_profile(_prefixed_path(request, reverse("comissoes:configure")), profile))
    else:
        form = CommissionSelectionForm(initial={"organs": selected_siglas}, choices=choices)

    generated_at = catalogo.get("generated_at")
    if isinstance(generated_at, datetime):
        generated_at = timezone.localtime(generated_at)

    context = {
        "form": form,
        "selected_count": len(selected_siglas),
        "selected_orgaos": selected_siglas,
        "all_orgaos": entries,
        "catalog_generated_at": generated_at,
        "index_url": _append_profile(_prefixed_path(request, reverse("comissoes:index")), profile),
        "profile": profile,
    }
    return render(request, "comissoes/manage_commissions.html", context)


def _apply_filters(queryset, tipos: Iterable[str], orgaos: Iterable[str], situacoes: Iterable[str]):
    if tipos:
        queryset = queryset.filter(sigla_tipo__in=list(tipos))
    if orgaos:
        queryset = queryset.filter(orgao_sigla__in=list(orgaos))
    if situacoes:
        queryset = queryset.filter(situacao__in=list(situacoes))
    return queryset


def propositions_api(request: HttpRequest) -> JsonResponse:
    tipos = _parse_multi(request, "tipos")
    orgaos = _parse_multi(request, "orgaos")
    situacoes = _parse_multi(request, "situacoes")
    search = request.GET.get("busca", "").strip()

    queryset = Proposition.objects.all()
    queryset = _apply_filters(queryset, tipos, orgaos, situacoes)
    selecionados = selected_orgao_siglas()
    if selecionados:
        queryset = queryset.filter(orgao_sigla__in=list(selecionados))
    if search:
        queryset = queryset.filter(ementa__icontains=search)

    data = [
        {
            "proposicao": prop.proposicao,
            "sigla_tipo": prop.sigla_tipo,
            "autor": prop.autor,
            "ementa": prop.ementa,
            "situacao": prop.situacao,
            "orgao": prop.orgao_sigla,
            "data_ultima_tramitacao": (
                timezone.localtime(prop.data_ultima_tramitacao).strftime("%d/%m/%Y %H:%M")
                if prop.data_ultima_tramitacao
                else ""
            ),
            "inteiro_teor_url": prop.inteiro_teor_url,
            "ficha_url": prop.ficha_tramitacao_url,
        }
        for prop in queryset.order_by("-data_ultima_tramitacao", "-updated_at")
    ]
    return JsonResponse({"results": data})


def export_xlsx(request: HttpRequest) -> HttpResponse:
    tipos = _parse_multi(request, "tipos")
    orgaos = _parse_multi(request, "orgaos")
    situacoes = _parse_multi(request, "situacoes")
    queryset = Proposition.objects.all()
    queryset = _apply_filters(queryset, tipos, orgaos, situacoes)
    selecionados = selected_orgao_siglas()
    if selecionados:
        queryset = queryset.filter(orgao_sigla__in=list(selecionados))
    data = list(
        queryset.order_by("-data_ultima_tramitacao").values(
            "proposicao",
            "autor",
            "ementa",
            "situacao",
            "orgao_sigla",
            "inteiro_teor_url",
            "ficha_tramitacao_url",
        )
    )
    df = pd.DataFrame(data)
    if not df.empty:
        df.rename(
            columns={
                "proposicao": "Proposição",
                "autor": "Autor",
                "ementa": "Ementa",
                "situacao": "Situação",
                "orgao_sigla": "Órgão",
                "inteiro_teor_url": "Inteiro Teor",
                "ficha_tramitacao_url": "Ficha de Tramitação",
            },
            inplace=True,
        )
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    filename = timezone.now().strftime("proposicoes_comissoes_%Y%m%d_%H%M%S.xlsx")
    response = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response
