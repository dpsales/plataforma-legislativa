from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, List

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...models import Event, MonitoredProposition, Proposition
from ...services import sync

IDENTIFIER_RE = re.compile(r"^([A-Z]+)\s*(\d+)/(\d{4})")


class Command(BaseCommand):
    help = "Importa dados do banco SQLite legado (agendaSemana.db) para o novo modelo Django."

    def add_arguments(self, parser):
        parser.add_argument(
            "--db-path",
            type=str,
            default=str(Path(settings.BASE_DIR) / "codUnificado" / "data" / "agendaSemana.db"),
            help="Caminho para o arquivo agendaSemana.db legado.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Limpa as tabelas antes de importar os dados do snapshot.",
        )

    def handle(self, *args, **options):
        db_path = Path(options["db_path"]).expanduser()
        if not db_path.exists():
            raise CommandError(f"Arquivo SQLite não encontrado em {db_path}")

        if options["clear"]:
            self.stdout.write("Limpando dados existentes...")
            MonitoredProposition.objects.all().delete()
            Event.objects.all().delete()
            Proposition.objects.all().delete()

        rows = self._fetch_rows(db_path)
        if not rows:
            self.stdout.write(self.style.WARNING("Nenhum registro encontrado no snapshot legado."))
            return

        proposition_entries: Dict[str, dict] = {}
        event_entries: List[dict] = []
        monitor_flags: Dict[str, dict] = {}

        for row in rows:
            identifier = (row.get("proposicao") or "").strip()
            if not identifier:
                continue

            if identifier not in proposition_entries:
                proposition_entries[identifier] = self._build_proposition_payload(identifier, row)
            else:
                self._merge_proposition_payload(proposition_entries[identifier], row)

            event_entries.append(self._build_event_payload(identifier, row))

            if str(row.get("marcarParaRelatorio") or "").upper() == "S":
                monitor_flags.setdefault(identifier, row)

        created = sync.upsert_catalog(proposition_entries.values())
        sync.upsert_events(event_entries)

        applied = 0
        for item in created:
            flag = monitor_flags.get(item.identifier)
            if not flag:
                continue
            MonitoredProposition.objects.update_or_create(
                proposition=item,
                defaults={
                    "destaque": True,
                    "observacoes": (flag.get("impactoFiscal") or flag.get("tipoImpactoFiscal") or "")[:500],
                    "selecionado_por": "import-snapshot",
                },
            )
            applied += 1

        self.stdout.write(self.style.SUCCESS(
            f"Importação concluída: {len(proposition_entries)} proposições, {len(event_entries)} eventos, {applied} monitoramentos."))

    def _fetch_rows(self, db_path: Path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute("SELECT * FROM eventos")
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def _build_proposition_payload(self, identifier: str, row: dict) -> dict:
        sigla_tipo, numero, ano = self._split_identifier(identifier)
        link_inteiro_teor = row.get("linkInteiroTeor") or ""
        if link_inteiro_teor.upper() == "N/A":
            link_inteiro_teor = ""
        return {
            "identifier": identifier,
            "casa": (row.get("casa") or "CD").strip()[:2],
            "sigla_tipo": sigla_tipo,
            "numero": numero,
            "ano": ano,
            "ementa": row.get("ementa") or "",
            "autor": row.get("autorPartidoUf") or "",
            "autor_partido_uf": row.get("autorPartidoUf") or "",
            "link_inteiro_teor": link_inteiro_teor,
            "link_ficha": row.get("linkComissaoPlenario") or "",
            "tem_pl": str(row.get("temPL") or "").upper() == "S",
            "impacto_fiscal": row.get("impactoFiscal") or "",
            "impacto_categoria": row.get("tipoImpactoFiscal") or "",
            "palavras_chave": row.get("buscaPalavrasChave") or "",
        }

    def _merge_proposition_payload(self, payload: dict, row: dict) -> None:
        if not payload.get("ementa") and row.get("ementa"):
            payload["ementa"] = row.get("ementa")
        if not payload.get("link_inteiro_teor") and row.get("linkInteiroTeor"):
            payload["link_inteiro_teor"] = row.get("linkInteiroTeor")
        if not payload.get("impacto_fiscal") and row.get("impactoFiscal"):
            payload["impacto_fiscal"] = row.get("impactoFiscal")
        if not payload.get("impacto_categoria") and row.get("tipoImpactoFiscal"):
            payload["impacto_categoria"] = row.get("tipoImpactoFiscal")

    def _build_event_payload(self, identifier: str, row: dict) -> dict:
        data_evento = row.get("dataEvento") or ""
        data_iso = ""
        if data_evento:
            try:
                dia, mes, ano = data_evento.split("/")
                data_iso = f"{int(ano):04d}-{int(mes):02d}-{int(dia):02d}"
            except ValueError:
                data_iso = ""
        link_colegiado = row.get("linkComissaoPlenario") or ""
        if link_colegiado.upper() == "N/A":
            link_colegiado = ""
        return {
            "identifier": identifier,
            "external_id": self._compose_event_id(row.get("evento_id"), identifier, data_iso, row.get("horaEvento")),
            "casa": (row.get("casa") or "CD").strip()[:2],
            "colegiado": row.get("nomeComissaoPlenario") or "",
            "data_evento": data_iso,
            "hora_evento": row.get("horaEvento") or "",
            "link_colegiado": link_colegiado,
            "plenario_ou_comissao": row.get("plenarioOuComissao") or "",
            "marcar_para_relatorio": str(row.get("marcarParaRelatorio") or "").upper() == "S",
        }

    def _split_identifier(self, identifier: str):
        match = IDENTIFIER_RE.match(identifier.replace(" ", ""))
        if match:
            sigla, numero, ano = match.groups()
            return sigla, numero, ano
        return "", "", ""

    def _compose_event_id(self, raw_id, identifier: str, data_iso: str, hora: str | None) -> str:
        raw = str(raw_id or "").strip()
        if raw:
            return raw
        parts = ["LEGACY", identifier.replace(" ", ""), data_iso or "0000-00-00", (hora or "00:00").replace(":", "")]
        return "-".join(parts)
