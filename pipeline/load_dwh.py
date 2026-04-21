"""Carga las dimensiones y tablas de hechos en BigQuery (dataset copperprint)."""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account

load_dotenv(Path(__file__).parent.parent / ".env")

_PROJECT  = os.getenv("BQ_PROJECT", "copperprint-dwh")
_DATASET  = os.getenv("BQ_DATASET", "copperprint")
_KEYFILE  = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    str(Path(__file__).parent.parent / "bigquery-credentials.json"),
)


def obtener_cliente() -> bigquery.Client:
    creds = service_account.Credentials.from_service_account_file(
        _KEYFILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return bigquery.Client(project=_PROJECT, credentials=creds)


def _cargar_tabla(cliente: bigquery.Client, df: pd.DataFrame, tabla: str) -> None:
    print(f"  Cargando {tabla} ({len(df)} filas)...")
    destino = f"{_PROJECT}.{_DATASET}.{tabla}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = cliente.load_table_from_dataframe(df, destino, job_config=job_config)
    job.result()


def cargar_dimensiones(cliente: bigquery.Client, dims: dict) -> None:
    print("Cargando dimensiones en BigQuery...")
    for nombre, df in dims.items():
        _cargar_tabla(cliente, df, f"dim_{nombre}")


def cargar_hechos(
    cliente: bigquery.Client,
    fact_consumo: pd.DataFrame,
    fact_produccion: pd.DataFrame,
) -> None:
    print("Cargando hechos en BigQuery...")
    _cargar_tabla(cliente, fact_consumo,    "fact_consumo_agua")
    _cargar_tabla(cliente, fact_produccion, "fact_produccion_empresa")


def verificar_carga(cliente: bigquery.Client) -> None:
    queries = {
        "dim_region (esperado 8)":       f"SELECT COUNT(*) FROM `{_PROJECT}.{_DATASET}.dim_region`",
        "dim_empresa (esperado 21)":     f"SELECT COUNT(*) FROM `{_PROJECT}.{_DATASET}.dim_empresa`",
        "fact_consumo_agua":             f"SELECT COUNT(*) FROM `{_PROJECT}.{_DATASET}.fact_consumo_agua`",
        "fact_produccion_empresa":       f"SELECT COUNT(*) FROM `{_PROJECT}.{_DATASET}.fact_produccion_empresa`",
    }
    print("\nVerificación BigQuery:")
    for desc, q in queries.items():
        try:
            resultado = list(cliente.query(q).result())[0][0]
            print(f"  {desc}: {resultado}")
        except Exception as e:
            print(f"  {desc}: ERROR — {e}")
