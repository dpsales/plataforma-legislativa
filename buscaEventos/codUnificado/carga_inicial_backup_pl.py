#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import pandas as pd

# --- 1) Configurações de caminhos --------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Caminho para o seu SQLite
DB_FILE = os.path.join(DATA_DIR, "agendaSemana.db")

# Caminho para o Excel de backup
EXCEL_FILE = os.path.join(BASE_DIR, "backup_pl.xlsx")


# --- 2) Criação da tabela backup_pl (se ainda não existir) -------
def init_db(conn: sqlite3.Connection):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS backup_pl (
        proposicao TEXT PRIMARY KEY,
        impactoFiscal TEXT,
        tipoImpactoFiscal TEXT,
        linkInteiroTeor TEXT,
        dataGeracaoPlanilha TEXT
    );
    """)
    conn.commit()


# --- 3) Leitura do Excel via pandas ------------------------------
def ler_excel_para_df(path_excel: str) -> pd.DataFrame:
    # As colunas esperadas: proposicao, impactoFiscal, tipoImpactoFiscal, linkInteiroTeor, dataGeracaoPlanilha
    df = pd.read_excel(path_excel, engine="openpyxl", dtype=str)
    # Preenche NaN com string vazia, se desejar
    df = df.fillna("")
    # Garante que a coluna 'proposicao' exista
    if "proposicao" not in df.columns:
        raise ValueError("Excel não contém a coluna obrigatória 'proposicao'.")
    return df[["proposicao", "impactoFiscal", "tipoImpactoFiscal", "linkInteiroTeor", "dataGeracaoPlanilha"]]


# --- 4) Upsert (INSERT OR REPLACE) no SQLite ----------------------
def carregar_para_sqlite(df: pd.DataFrame, conn: sqlite3.Connection):
    sql = """
    INSERT OR REPLACE INTO backup_pl
      (proposicao, impactoFiscal, tipoImpactoFiscal, linkInteiroTeor, dataGeracaoPlanilha)
    VALUES (?, ?, ?, ?, ?);
    """
    registros = df.itertuples(index=False, name=None)
    conn.executemany(sql, registros)
    conn.commit()


def main():
    # abre conexão
    with sqlite3.connect(DB_FILE) as conn:
        print(f"[LOG] Conectando em SQLite: {DB_FILE}")
        # inicializa tabela
        init_db(conn)
        print("[LOG] Tabela 'backup_pl' criada (se não existia).")

        # lê Excel
        print(f"[LOG] Lendo Excel: {EXCEL_FILE}")
        df_backup = ler_excel_para_df(EXCEL_FILE)
        print(f"[LOG] {len(df_backup)} registros lidos do Excel.")

        # carrega no SQLite
        print("[LOG] Carregando registros em 'backup_pl'...")
        carregar_para_sqlite(df_backup, conn)
        print(f"[LOG] Concluído! {len(df_backup)} registros inseridos/atualizados em backup_pl.")

if __name__ == "__main__":
    main()
