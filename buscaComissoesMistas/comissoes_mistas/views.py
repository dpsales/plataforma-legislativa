from __future__ import annotations

from datetime import datetime
from typing import Iterable

import io
import pandas as pd
from django.db.models import Max, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from .models import Proposition
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


def index(request: HttpRequest) -> HttpResponse:
    tipos = Proposition.objects.order_by().values_list("sigla_tipo", flat=True).distinct()
    comissoes = Proposition.objects.order_by().values_list("comissao", flat=True).distinct()
    situacoes = Proposition.objects.order_by().values_list("situacao", flat=True).distinct()
    last_update = Proposition.objects.aggregate(last=Max("updated_at"))["last"] or timezone.now()
    catalogo = fetch_commission_catalog()

    catalog_senate = catalogo.get("senate", []) or []
    catalog_mixed = catalogo.get("mixed", []) or []

    seen_siglas: set[str] = set()
    all_commissions: list[dict[str, str]] = []

    def _append(sigla: str | None, nome: str | None, origem: str) -> None:
        if not sigla:
            return
        sigla_norm = sigla.strip().upper()
        if not sigla_norm or sigla_norm in seen_siglas:
            return
        seen_siglas.add(sigla_norm)
        label = (nome or "").strip()
        all_commissions.append({"sigla": sigla_norm, "nome": label, "origem": origem})

    for entry in catalog_senate:
        _append(entry.get("sigla"), entry.get("nome"), "senado")

    for entry in catalog_mixed:
        _append(entry.get("sigla"), entry.get("nome"), "mista")

    for value in comissoes:
        if value:
            _append(value, value, "dataset")

    all_commissions.sort(key=lambda item: item["sigla"])

    generated_at = catalogo.get("generated_at")
    if isinstance(generated_at, datetime):
        generated_at = timezone.localtime(generated_at)

    context = {
        "types": [value for value in tipos if value],
        "comissoes": [value for value in comissoes if value],
        "situacoes": [value for value in situacoes if value],
        "all_commissions": all_commissions,
        "last_update": timezone.localtime(last_update),
        "api_url": _prefixed_path(request, reverse("comissoes:propositions-api")),
        "export_url": _prefixed_path(request, reverse("comissoes:export-xlsx")),
        "static_prefix": _prefixed_path(request, "static").rstrip("/"),
        "catalog_senate": catalog_senate,
        "catalog_mixed": catalog_mixed,
        "catalog_generated_at": generated_at,
    }
    return render(request, "comissoes/index.html", context)


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
