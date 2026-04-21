"""Extrae los datos crudos de los archivos COCHILCO y los retorna como DataFrames normalizados."""

from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).parent.parent / "data" / "raw" / "cochilco"

_CONSUMO    = RAW / "consumo_agua_2024.xlsx"
_PROYECCION = RAW / "proyeccion_demanda_2025_2034.xlsx"
_PRODUCCION = RAW / "produccion_empresa_tabla17.xlsx"

_MES_MAP = {
    "ENE": 1, "JAN": 1, "FEB": 2, "MAR": 3,
    "ABR": 4, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "AUG": 8, "SEP": 9,
    "OCT": 10, "NOV": 11, "DIC": 12, "DEC": 12,
}


def _a_float(val) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        f = float(val)
        return None if np.isnan(f) else f
    s = str(val).strip()
    if s in ("", "-", "SD", "n/d", "N/D", "nan"):
        return None
    try:
        return float(s.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _parse_año(v) -> int | None:
    try:
        año = int(float(str(v)))
        return año if 2000 <= año <= 2040 else None
    except (ValueError, TypeError):
        return None


def _wide_a_long(df: pd.DataFrame, fila_años: int, filas_datos: list[int]) -> pd.DataFrame:
    cols_año = {i: a for i, v in enumerate(df.iloc[fila_años]) if (a := _parse_año(v))}

    filas = []
    for fi in filas_datos:
        row = df.iloc[fi]
        nombre = str(row.iloc[1]).strip()
        unidad = str(row.iloc[2]).strip() if df.shape[1] > 2 else ""
        if not nombre or nombre == "nan":
            continue
        for ci, año in cols_año.items():
            val = _a_float(row.iloc[ci])
            if val is not None:
                filas.append({"nombre": nombre, "unidad": unidad, "anio": año, "valor_ls": val})

    return pd.DataFrame(filas)


def _parse_periodo(s: str) -> tuple[int | None, int | None]:
    s = s.strip().upper().replace("(P)", "")
    try:
        yr = int(s)
        return (yr, None) if 2000 <= yr <= 2035 else (None, None)
    except ValueError:
        pass
    partes = s.split()
    año = None
    for p in partes:
        digitos = "".join(c for c in p if c.isdigit())
        if len(digitos) == 4 and 2000 <= int(digitos) <= 2035:
            año = int(digitos)
            break
    abrev = partes[0].split("/")[0] if partes else ""
    return año, _MES_MAP.get(abrev)


def _limpiar_nombre(val) -> str:
    s = str(val).strip()
    return "" if s in ("nan", "None", "") else s.replace("\n", " ")


def _extraer_uso_fuente(df: pd.DataFrame) -> pd.DataFrame:
    return _wide_a_long(df, fila_años=3, filas_datos=[4, 5, 6, 7])


def _extraer_extraccion_subtipos(df: pd.DataFrame) -> pd.DataFrame:
    return _wide_a_long(df, fila_años=12, filas_datos=[13, 14, 15, 16, 17, 18, 19, 20])


def _extraer_extraccion_regional(df: pd.DataFrame) -> pd.DataFrame:
    cols_año = {i: a for i, v in enumerate(df.iloc[25]) if (a := _parse_año(v))}

    filas = []
    for i in range(26, 50, 3):
        nombre_region = str(df.iloc[i, 1]).strip()
        if not nombre_region or nombre_region == "nan":
            continue
        for offset, tipo in [(1, "continental"), (2, "mar")]:
            if i + offset >= len(df):
                break
            row = df.iloc[i + offset]
            for ci, año in cols_año.items():
                val = _a_float(row.iloc[ci])
                if val is not None:
                    filas.append({"region": nombre_region, "tipo": tipo, "anio": año, "valor_ls": val})

    return pd.DataFrame(filas)


def _extraer_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    recirculacion    = _wide_a_long(df, fila_años=3,  filas_datos=[4, 5])
    consumo_unitario = _wide_a_long(df, fila_años=11, filas_datos=[12, 13])
    return pd.concat([recirculacion, consumo_unitario], ignore_index=True)


def _extraer_consumo_proceso(df: pd.DataFrame) -> pd.DataFrame:
    return _wide_a_long(df, fila_años=19, filas_datos=[20, 21, 22, 23, 24, 25, 26])


def _extraer_proyecciones(df: pd.DataFrame) -> pd.DataFrame:
    filas_datos = [
        i for i in range(4, min(30, len(df)))
        if str(df.iloc[i, 1]).strip() not in ("", "nan")
    ]
    return _wide_a_long(df, fila_años=3, filas_datos=filas_datos)


def _extraer_produccion_empresa(df: pd.DataFrame) -> pd.DataFrame:
    empresas: dict[int, str] = {}
    for col in range(1, df.shape[1] - 1):
        grupo = _limpiar_nombre(df.iloc[0, col])
        sub   = _limpiar_nombre(df.iloc[1, col])
        if not grupo and not sub:
            continue
        empresas[col] = f"{grupo} - {sub}" if grupo and sub else (grupo or sub)

    filas = []
    for row_idx in [2, 4, 6, 8, 10]:
        if row_idx >= len(df):
            break
        raw_row      = df.iloc[row_idx]
        periodos_raw = str(raw_row.iloc[0]).split("\n")

        parsed: list[tuple[int | None, int | None]] = []
        año_actual = None
        for p in periodos_raw:
            año, mes = _parse_periodo(p)
            if año is not None:
                año_actual = año
            if mes is not None:
                parsed.append((año_actual, mes))
            elif año is not None:
                parsed.append((año, None))

        for col, empresa in empresas.items():
            valores = str(raw_row.iloc[col]).split("\n")
            for i, (año, mes) in enumerate(parsed):
                if i >= len(valores):
                    break
                val = _a_float(valores[i])
                if val is not None and año is not None:
                    filas.append({"empresa": empresa, "anio": año, "mes": mes, "miles_tm_cu_fino": val})

    return pd.DataFrame(filas)


def extraer_todo() -> dict[str, pd.DataFrame]:
    df_uso_ext  = pd.read_excel(_CONSUMO,    sheet_name="Uso y Extracción de Agua", header=None)
    df_indicadores = pd.read_excel(_CONSUMO, sheet_name="Indicadores de Gestión",   header=None)
    df_salidas  = pd.read_excel(_CONSUMO,    sheet_name="Salidas de Agua",           header=None)
    df_proyec   = pd.read_excel(_PROYECCION, sheet_name="Demanda de agua 2025-34",   header=None)
    df_prod     = pd.read_excel(_PRODUCCION, sheet_name="Sheet1", header=None, dtype=str)

    return {
        "uso_fuente":          _extraer_uso_fuente(df_uso_ext),
        "extraccion_subtipos": _extraer_extraccion_subtipos(df_uso_ext),
        "extraccion_regional": _extraer_extraccion_regional(df_uso_ext),
        "indicadores":         _extraer_indicadores(df_indicadores),
        "consumo_proceso":     _extraer_consumo_proceso(df_salidas),
        "proyecciones":        _extraer_proyecciones(df_proyec),
        "produccion_empresa":  _extraer_produccion_empresa(df_prod),
    }
