"""Carga las dimensiones y tablas de hechos en SQL Server."""

import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).parent.parent / ".env")


def obtener_engine():
    pwd = quote_plus(os.getenv("SA_PASSWORD", ""))
    url = f"mssql+pyodbc://sa:{pwd}@localhost:1433/copperprint_oltp?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    return create_engine(url, fast_executemany=True)


def _cargar_tabla(engine, df: pd.DataFrame, tabla: str, chunk: int = 500) -> None:
    print(f"  Cargando {tabla} ({len(df)} filas)...")
    df.to_sql(tabla, engine, schema="cp", if_exists="append", index=False, chunksize=chunk)


def cargar_dimensiones(engine, dims: dict) -> None:
    print("Cargando dimensiones...")
    _cargar_tabla(engine, dims["tiempo"],  "dim_tiempo")
    _cargar_tabla(engine, dims["region"],  "dim_region")
    _cargar_tabla(engine, dims["fuente"],  "dim_fuente")
    _cargar_tabla(engine, dims["proceso"], "dim_proceso")
    _cargar_tabla(engine, dims["empresa"], "dim_empresa")


def cargar_hechos(engine, fact_consumo: pd.DataFrame, fact_produccion: pd.DataFrame) -> None:
    print("Cargando hechos...")
    _cargar_tabla(engine, fact_consumo,    "fact_consumo_agua")
    _cargar_tabla(engine, fact_produccion, "fact_produccion_empresa")


def verificar_carga(engine) -> None:
    queries = {
        "dim_region (esperado 8)":          "SELECT COUNT(*) FROM cp.dim_region",
        "dim_empresa (esperado ~21)":        "SELECT COUNT(*) FROM cp.dim_empresa",
        "fact_consumo_agua":                 "SELECT COUNT(*) FROM cp.fact_consumo_agua",
        "fact_produccion_empresa":           "SELECT COUNT(*) FROM cp.fact_produccion_empresa",
        "extracción total 2024 (m3/año)":   """
            SELECT SUM(f.volumen_m3_anual) / 1e6
            FROM cp.fact_consumo_agua f
            JOIN cp.dim_tiempo t ON f.id_tiempo = t.id_tiempo
            JOIN cp.dim_fuente fu ON f.id_fuente = fu.id_fuente
            WHERE t.anio = 2024 AND t.es_anual = 1
              AND f.id_region IS NULL AND f.es_proyeccion = 0
              AND fu.nombre_fuente = 'Agua Total Utilizada'
        """,
    }
    print("\nVerificación de carga:")
    with engine.connect() as conn:
        for desc, q in queries.items():
            try:
                result = conn.execute(text(q)).scalar()
                print(f"  {desc}: {result}")
            except Exception as e:
                print(f"  {desc}: ERROR — {e}")
