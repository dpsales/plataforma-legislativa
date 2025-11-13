# update_backup_pl.py
"""
Atualiza/insere registros na tabela backup_pl a partir de um XLSX.
Basta abrir no VS Code, ajustar EXCEL_PATH e pressionar F5.
"""

import pandas as pd
import sqlite3
from pathlib import Path

# ------------- CONFIGURÁVEL ---------------------------------------
EXCEL_PATH = Path(__file__).resolve().parent / "backup_pl.xlsx"   # <- AJUSTE AQUI

# ---------------- infra do banco ----------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE  = DATA_DIR / "agendaSemana.db"

def get_conn():
    """Conexão SQLite em autocommit (isolation_level=None)."""
    return sqlite3.connect(DB_FILE, isolation_level=None)

def ensure_table():
    with get_conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS backup_pl (
                proposicao          TEXT PRIMARY KEY,
                impactoFiscal       TEXT,
                tipoImpactoFiscal   TEXT,
                linkInteiroTeor     TEXT,
                dataGeracaoPlanilha TEXT
            );
        """)

# ---------------- carga do XLSX -----------------------------------
def carregar_excel():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {EXCEL_PATH}")

    df = pd.read_excel(EXCEL_PATH)

    # Mapeia/filtra colunas sem se importar com maiúsc-minúsc
    rename = {
        "proposicao"          : "proposicao",
        "impactofiscal"       : "impactoFiscal",
        "tipoimpactofiscal"   : "tipoImpactoFiscal",
        "linkinteiroteor"     : "linkInteiroTeor",
        "datageracaoplanilha" : "dataGeracaoPlanilha",
    }
    df = (
        df.rename(columns={c: rename[c.lower()] for c in df.columns
                           if c.lower() in rename})
          .reindex(columns=rename.values())
          .fillna("")
    )

    if df.empty:
        print("[WARN] Planilha vazia ou colunas obrigatórias ausentes.")
        return

    ensure_table()

    with get_conn() as con:
        cur = con.cursor()
        sql = """
            INSERT INTO backup_pl
                  (proposicao, impactoFiscal, tipoImpactoFiscal,
                   linkInteiroTeor, dataGeracaoPlanilha)
            VALUES (?,?,?,?,?)
            ON CONFLICT(proposicao) DO UPDATE SET
                 impactoFiscal       = excluded.impactoFiscal,
                 tipoImpactoFiscal   = excluded.tipoImpactoFiscal,
                 linkInteiroTeor     = excluded.linkInteiroTeor,
                 dataGeracaoPlanilha = excluded.dataGeracaoPlanilha;
        """
        for row in df.itertuples(index=False):
            cur.execute(sql, row)

    print(f"[LOG] {len(df)} linhas inseridas/atualizadas em backup_pl.")

# ---------------- MAIN --------------------------------------------
if __name__ == "__main__":
    try:
        carregar_excel()
        print("[LOG] Importação concluída com sucesso.")
    except Exception as exc:
        print(f"[ERROR] {exc}")
