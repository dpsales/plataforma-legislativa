"""
Módulo de integração entre o script buscaReqs15.py e Django.
Permite popular o banco de dados com requerimentos da Câmara e Senado.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, date
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import requests

from .models import Requerimento

logger = logging.getLogger(__name__)


class ImportadorRequerimentos:
    """Importa requerimentos para o banco de dados Django."""

    @staticmethod
    def from_proposition(prop_dict: dict[str, Any]) -> None:
        """
        Cria ou atualiza um requerimento baseado em um dicionário
        com dados de uma proposição (vindo do buscaReqs15.py).
        
        Args:
            prop_dict: Dicionário com dados da proposição
        """
        codigo = prop_dict.get("CodigoMateria") or prop_dict.get("codigo_material") or ""
        
        if not codigo:
            logger.warning("Proposição sem código, ignorando")
            return

        # Conversão de datas
        data_apresentacao = _parse_date(prop_dict.get("DataApresentacao"))
        data_ultima_tramitacao = _parse_date(prop_dict.get("DataUltimaTramitacao"))

        # Cria ou atualiza
        requerimento, criado = Requerimento.objects.update_or_create(
            codigo_material=str(codigo).strip(),
            defaults={
                "titulo": prop_dict.get("Titulo", ""),
                "autor": prop_dict.get("Autor", ""),
                "ementa": prop_dict.get("Ementa", ""),
                "situacao": prop_dict.get("SituacaoAtual", ""),
                "data_apresentacao": data_apresentacao,
                "data_ultima_tramitacao": data_ultima_tramitacao,
                "descricao_ultima_tramitacao": prop_dict.get("DescricaoUltimaTramitacao", ""),
                "link_ficha": prop_dict.get("LinkFicha", ""),
                "link_inteiro_teor": prop_dict.get("LinkInteiroTeor", ""),
                "termos_encontrados": prop_dict.get("TermosEncontrados", ""),
                "grupos_encontrados": prop_dict.get("GruposEncontrados", ""),
                "assuntos_encontrados": prop_dict.get("AssuntosEncontrados", ""),
                "local": prop_dict.get("Local", ""),
                "casa": prop_dict.get("Casa", ""),
            }
        )

        acao = "criado" if criado else "atualizado"
        logger.debug(f"Requerimento {codigo} {acao}")

        return requerimento

    @staticmethod
    def from_dataframe(df: pd.DataFrame) -> tuple[int, int, int]:
        """
        Importa registros a partir de um DataFrame.

        Retorna: (criados, atualizados, erros)
        """
        criados = 0
        atualizados = 0
        erros = 0

        if df.empty:
            return criados, atualizados, erros

        df = df.fillna("")
        df.columns = [str(col).strip() for col in df.columns]

        columns = set(df.columns)
        if _is_proposicoes_schema(columns):
            for idx, row in enumerate(df.to_dict(orient="records"), 1):
                try:
                    resultado = ImportadorRequerimentos.from_proposition(row)
                    if resultado:
                        criados += 1
                except Exception as e:
                    logger.error(f"Erro ao importar linha {idx}: {e}")
                    erros += 1
        elif _is_autores_schema(columns):
            criados, atualizados, erros = _importar_de_autores(df, sleep_seconds=0.1)
        else:
            raise ValueError(
                "Formato de arquivo desconhecido. "
                "Esperado: colunas de proposicoes (ex: CodigoMateria) "
                "ou autores (ex: idProposicao)."
            )

        return criados, atualizados, erros

    @staticmethod
    def from_file(
        file_obj,
        filename: str,
        delimiter: str = ";",
        sheet: str | int | None = None,
        sleep_seconds: float = 0.1,
    ) -> tuple[int, int, int]:
        """
        Importa registros a partir de um arquivo CSV ou Excel.

        Args:
            file_obj: arquivo aberto (Upload Django ou handle local)
            filename: nome do arquivo para detecao de extensao
            delimiter: delimitador CSV
            sheet: aba do Excel (nome ou indice)
            sleep_seconds: pausa entre chamadas a API (autores)
        """
        suffix = Path(filename).suffix.lower()
        if suffix == ".csv":
            df = pd.read_csv(file_obj, sep=delimiter, dtype=str, encoding="utf-8")
        elif suffix in {".xlsx", ".xls"}:
            sheet_name = sheet if sheet not in (None, "") else 0
            df = pd.read_excel(file_obj, sheet_name=sheet_name, dtype=str)
        else:
            raise ValueError("Arquivo deve ser CSV ou Excel (.xlsx/.xls)")

        df = df.fillna("")
        df.columns = [str(col).strip() for col in df.columns]
        columns = set(df.columns)

        if _is_proposicoes_schema(columns):
            return ImportadorRequerimentos.from_dataframe(df)
        if _is_autores_schema(columns):
            return _importar_de_autores(df, sleep_seconds=sleep_seconds)

        raise ValueError(
            "Formato de arquivo desconhecido. "
            "Esperado: colunas de proposicoes (ex: CodigoMateria) "
            "ou autores (ex: idProposicao)."
        )

    @staticmethod
    def from_propositions(propositions: list[dict]) -> tuple[int, int]:
        """
        Importa uma lista de proposições para o banco.
        
        Args:
            propositions: Lista de dicionários com dados de proposições
            
        Returns:
            Tupla (quantidade_criada, quantidade_atualizada)
        """
        criados = 0
        atualizados = 0

        for prop in propositions:
            requerimento = ImportadorRequerimentos.from_proposition(prop)
            if requerimento:
                # Verificar se foi criado na mesma requisição
                # (não é 100% preciso, mas funciona para logging)
                criados += 1

        return criados, atualizados

    @staticmethod
    def limpar_antigos(dias: int = 90) -> int:
        """
        Remove requerimentos não atualizados há mais de N dias.
        
        Args:
            dias: Número de dias para considerar como "antigo"
            
        Returns:
            Número de requerimentos removidos
        """
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=dias)
        antigos = Requerimento.objects.filter(data_atualizacao__lt=cutoff)
        count = antigos.count()
        antigos.delete()

        logger.info(f"{count} requerimentos antigos removidos (> {dias} dias)")
        return count


def _parse_date(value: str | None) -> date | None:
    """
    Converte string de data em objeto date.
    Suporta múltiplos formatos de data.
    """
    if not value or not str(value).strip():
        return None

    value_str = str(value).strip()

    # Tenta múltiplos formatos
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M:%S"]:
        try:
            dt = datetime.strptime(value_str, fmt)
            return dt.date()
        except ValueError:
            continue

    logger.warning(f"Não foi possível parsear data: {value}")
    return None


def _is_proposicoes_schema(columns: set[str]) -> bool:
    return "CodigoMateria" in columns or "codigo_material" in columns


def _is_autores_schema(columns: set[str]) -> bool:
    return "idProposicao" in columns and "nomeAutor" in columns


def _importar_de_autores(df: pd.DataFrame, sleep_seconds: float) -> tuple[int, int, int]:
    criados = 0
    atualizados = 0
    erros = 0

    df = df.fillna("")
    if "ordemAssinatura" in df.columns:
        df["ordemAssinatura"] = df["ordemAssinatura"].astype(str)

    for prop_id, group in df.groupby("idProposicao"):
        try:
            detail = _fetch_proposicao_detail(prop_id)
            if not detail:
                erros += 1
                continue

            autores = _build_autores(group)
            dados = _build_proposicao_dict(detail, autores)
            resultado = ImportadorRequerimentos.from_proposition(dados)
            if resultado:
                criados += 1
            if sleep_seconds:
                time.sleep(sleep_seconds)
        except Exception as e:
            logger.error(f"Erro ao importar proposicao {prop_id}: {e}")
            erros += 1

    return criados, atualizados, erros


def _build_autores(group: pd.DataFrame) -> str:
    autores: list[str] = []
    try:
        group = group.sort_values(by=["ordemAssinatura"], key=lambda s: s.map(_safe_int))
    except Exception:
        pass

    for _, row in group.iterrows():
        nome = str(row.get("nomeAutor", "")).strip()
        partido = str(row.get("siglaPartidoAutor", "")).strip()
        uf = str(row.get("siglaUFAutor", "")).strip()
        if not nome:
            continue
        suffix = "/".join([value for value in (partido, uf) if value])
        autores.append(f"{nome} ({suffix})" if suffix else nome)

    return "; ".join(autores)


def _fetch_proposicao_detail(prop_id: str) -> dict:
    url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{prop_id}"
    response = requests.get(url, timeout=45)
    response.raise_for_status()
    return response.json().get("dados", {})


def _build_proposicao_dict(detail: dict, autores: str) -> dict:
    ultimo_status = detail.get("ultimoStatus", {})
    local_orgao = ultimo_status.get("orgao", {})

    titulo = f"{detail.get('siglaTipo', '')} {detail.get('numero', '')}/{detail.get('ano', '')}".strip()
    ficha = detail.get("urlProposicao") or (
        f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={detail.get('id')}"
        if detail.get("id")
        else ""
    )

    return {
        "CodigoMateria": titulo,
        "Titulo": titulo,
        "Autor": autores,
        "Ementa": detail.get("ementaDetalhada") or detail.get("ementa") or "",
        "SituacaoAtual": ultimo_status.get("descricaoSituacao", ""),
        "DataApresentacao": detail.get("dataApresentacao", ""),
        "DataUltimaTramitacao": ultimo_status.get("dataHora", ""),
        "DescricaoUltimaTramitacao": ultimo_status.get("descricaoTramitacao", ""),
        "LinkFicha": ficha,
        "LinkInteiroTeor": detail.get("urlInteiroTeor", ""),
        "TermosEncontrados": "",
        "GruposEncontrados": "",
        "AssuntosEncontrados": "",
        "Local": local_orgao.get("sigla") or local_orgao.get("nomePublicacao") or "",
        "Casa": "Câmara",
    }


def _safe_int(value) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return 0
