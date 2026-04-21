"""Construye las dimensiones y tablas de hechos normalizadas desde los DataFrames crudos."""

import pandas as pd

_REGIONES = [
    ("XV", "XV Arica y Parinacota", "norte grande"),
    ("I",  "I Tarapacá",            "norte grande"),
    ("II", "II Antofagasta",         "norte grande"),
    ("III","III Atacama",            "norte chico"),
    ("IV", "IV Coquimbo",            "norte chico"),
    ("V",  "V Valparaíso",           "central"),
    ("VI", "VI O'Higgins",           "central"),
    ("RM", "RM Metropolitana",       "central"),
]

_FUENTES = [
    ("Agua Continental",               "continental", False),
    ("Agua de Mar",                    "mar",         False),
    ("Agua Reutilizada y Recirculada", "recirculada", True),
    ("Extracción Agua Continental",    "continental", False),
    ("Agua superficial",               "continental", False),
    ("Agua subterránea",               "continental", False),
    ("Agua adquirida a terceros",      "terceros",    False),
    ("Extracción Agua de Mar",         "mar",         False),
    ("Agua de mar desalada",           "mar",         False),
    ("Agua de mar sin desalar",        "mar",         False),
    ("Agua continental",               "continental", False),
    ("Agua de mar",                    "mar",         False),
]

_PROCESOS = [
    ("Agua mina / Control de polvo",        "extraccion"),
    ("Concentración / Depósito de relaves", "procesamiento"),
    ("Hidrometalurgia",                     "procesamiento"),
    ("Servicios",                           "apoyo"),
    ("Fundición / Refinería",               "procesamiento"),
    ("Otras tareas operativas",             "apoyo"),
]

_EMPRESAS = [
    ("CODELCO - Total(1)",                                      "Codelco",              "estatal"),
    ("Chuquicamata, Radomiro Tomic y Ministro Hales",           "Codelco",              "estatal"),
    ("Salvador",                                                "Codelco",              "estatal"),
    ("Andina",                                                  "Codelco",              "estatal"),
    ("El Teniente",                                             "Codelco",              "estatal"),
    ("Minera Gaby",                                             "Codelco",              "estatal"),
    ("Escondida",                                               "BHP",                  "privada"),
    ("Collahuasi",                                              "Collahuasi",           "privada"),
    ("Los Pelambres",                                           "Antofagasta Minerals", "privada"),
    ("Anglo American Sur",                                      "Anglo American",       "privada"),
    ("El Abra",                                                 "Freeport",             "privada"),
    ("Candelaria",                                              "Lundin Mining",        "privada"),
    ("Mantos Copper",                                           "Mantos Copper",        "privada"),
    ("Zaldivar",                                                "Antofagasta Minerals", "privada"),
    ("Cerro Colorado",                                          "BHP",                  "privada"),
    ("Centinela (Oxidos)",                                      "Antofagasta Minerals", "privada"),
    ("Quebrada Blanca",                                         "Teck",                 "privada"),
    ("Lomas Bayas",                                             "Glencore",             "privada"),
    ("Centinela (Súlfuros)",                                    "Antofagasta Minerals", "privada"),
    ("Spence",                                                  "BHP",                  "privada"),
    ("Otros / Other",                                           None,                   "privada"),
]


def _dim_tiempo(dfs: dict) -> pd.DataFrame:
    años: set[int] = set()
    meses: set[tuple[int, int]] = set()
    for df in dfs.values():
        if "anio" in df.columns:
            años.update(int(a) for a in df["anio"].dropna().unique())
        if "mes" in df.columns:
            for _, row in df[["anio", "mes"]].dropna(subset=["mes"]).iterrows():
                meses.add((int(row["anio"]), int(row["mes"])))
    filas = []
    for a in sorted(años):
        filas.append({"id_tiempo": a, "anio": a, "mes": None, "trimestre": None, "es_anual": 1})
    for a, m in sorted(meses):
        filas.append({"id_tiempo": a * 100 + m, "anio": a, "mes": m, "trimestre": (m - 1) // 3 + 1, "es_anual": 0})
    return pd.DataFrame(filas).drop_duplicates("id_tiempo")


def _dim_region() -> pd.DataFrame:
    df = pd.DataFrame([{"codigo_region": c, "nombre_region": n, "zona": z} for c, n, z in _REGIONES])
    df.insert(0, "id_region", range(1, len(df) + 1))
    return df


def _dim_fuente() -> pd.DataFrame:
    df = pd.DataFrame([{"nombre_fuente": n, "categoria": c, "es_recirculada": int(r)} for n, c, r in _FUENTES])
    df.insert(0, "id_fuente", range(1, len(df) + 1))
    return df


def _dim_proceso() -> pd.DataFrame:
    df = pd.DataFrame([{"nombre_proceso": n, "etapa": e} for n, e in _PROCESOS])
    df.insert(0, "id_proceso", range(1, len(df) + 1))
    return df


def _dim_empresa() -> pd.DataFrame:
    df = pd.DataFrame([{"nombre_empresa": n, "grupo_controlador": g, "tipo": t} for n, g, t in _EMPRESAS])
    df.insert(0, "id_empresa", range(1, len(df) + 1))
    return df


def construir_dimensiones(dfs: dict) -> dict:
    return {
        "tiempo":  _dim_tiempo(dfs),
        "region":  _dim_region(),
        "fuente":  _dim_fuente(),
        "proceso": _dim_proceso(),
        "empresa": _dim_empresa(),
    }


def _id_tiempo_series(anio: pd.Series, mes: pd.Series | None = None) -> pd.Series:
    if mes is None:
        return anio.astype(int)
    return anio.astype(int) * 100 + mes.fillna(0).astype(int)


def _volumen(ls: pd.Series) -> pd.Series:
    return (ls * 31536).round(2)


def construir_fact_consumo(dfs: dict, dims: dict) -> pd.DataFrame:
    fuente_id = dims["fuente"].set_index("nombre_fuente")["id_fuente"]
    region_id = dims["region"].set_index("codigo_region")["id_region"]
    proceso_id = dims["proceso"].set_index("nombre_proceso")["id_proceso"]

    partes = []

    df = dfs["uso_fuente"].copy()
    df["id_tiempo"]  = df["anio"].astype(int)
    df["id_fuente"]  = df["nombre"].map(fuente_id)
    df["id_region"]  = None
    df["id_proceso"] = None
    df["es_proyeccion"] = 0
    partes.append(df.dropna(subset=["id_fuente"]))

    df = dfs["extraccion_regional"].copy()
    df["id_tiempo"] = df["anio"].astype(int)
    df["id_fuente"] = df["tipo"].map({
        "continental": fuente_id.get("Extracción Agua Continental"),
        "mar":         fuente_id.get("Extracción Agua de Mar"),
    })
    df["id_region"]  = df["region"].str.split().str[0].map(region_id)
    df["id_proceso"] = None
    df["es_proyeccion"] = 0
    partes.append(df.dropna(subset=["id_fuente", "id_region"]))

    id_f_base = int(fuente_id.get("Agua Continental", 1))
    df = dfs["consumo_proceso"].copy()
    df["id_tiempo"]  = df["anio"].astype(int)
    df["id_fuente"]  = id_f_base
    df["id_region"]  = None
    df["id_proceso"] = df["nombre"].map(proceso_id)
    df["es_proyeccion"] = 0
    partes.append(df.dropna(subset=["id_proceso"]))

    df = dfs["proyecciones"].copy()
    df["id_tiempo"]  = df["anio"].astype(int)
    df["id_fuente"]  = df["nombre"].map(fuente_id)
    df["id_region"]  = None
    df["id_proceso"] = None
    df["es_proyeccion"] = 1
    partes.append(df.dropna(subset=["id_fuente"]))

    cols = ["id_tiempo", "id_fuente", "id_region", "id_proceso", "caudal_ls", "volumen_m3_anual", "es_proyeccion"]
    result = pd.concat(partes, ignore_index=True)
    result = result.rename(columns={"valor_ls": "caudal_ls"})
    result["caudal_ls"] = result["caudal_ls"].astype(float)
    result["volumen_m3_anual"] = _volumen(result["caudal_ls"])
    for c in ("id_tiempo", "id_fuente", "id_proceso"):
        result[c] = result[c].where(result[c].notna(), other=None)
    return result[cols].reset_index(drop=True)


def construir_fact_produccion(df_prod: pd.DataFrame, dims: dict) -> pd.DataFrame:
    empresa_id = dims["empresa"].set_index("nombre_empresa")["id_empresa"]

    df = df_prod.copy()
    df["mes_safe"] = df["mes"].where(df["mes"].notna(), other=0).astype(int)
    df["id_tiempo"] = df.apply(
        lambda r: int(r["anio"]) if r["mes_safe"] == 0 else int(r["anio"]) * 100 + r["mes_safe"],
        axis=1,
    )
    df["id_empresa"] = df["empresa"].map(empresa_id)
    df["es_anual"]   = (df["mes_safe"] == 0).astype(int)
    df = df.dropna(subset=["id_empresa", "id_tiempo"])
    return df[["id_tiempo", "id_empresa", "miles_tm_cu_fino", "es_anual"]].reset_index(drop=True)
