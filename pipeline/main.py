"""Orquesta el pipeline ETL completo: extracción → transformación → carga OLTP y DWH."""

from pipeline import extract, transform, load_oltp, load_dwh


def run():
    print("=== CopperPrint ETL ===")

    print("\n[1/3] Extrayendo datos COCHILCO...")
    dfs = extract.extraer_todo()
    for nombre, df in dfs.items():
        print(f"  {nombre}: {len(df)} registros")

    print("\n[2/3] Construyendo dimensiones y hechos...")
    dims = transform.construir_dimensiones(dfs)
    fact_consumo    = transform.construir_fact_consumo(dfs, dims)
    fact_produccion = transform.construir_fact_produccion(dfs["produccion_empresa"], dims)
    print(f"  fact_consumo_agua:          {len(fact_consumo)} filas")
    print(f"  fact_produccion_empresa:    {len(fact_produccion)} filas")

    print("\n[3/3] Cargando en SQL Server (OLTP)...")
    engine = load_oltp.obtener_engine()
    load_oltp.cargar_dimensiones(engine, dims)
    load_oltp.cargar_hechos(engine, fact_consumo, fact_produccion)
    load_oltp.verificar_carga(engine)

    print("\n[4/4] Cargando en BigQuery (DWH)...")
    cliente = load_dwh.obtener_cliente()
    load_dwh.cargar_dimensiones(cliente, dims)
    load_dwh.cargar_hechos(cliente, fact_consumo, fact_produccion)
    load_dwh.verificar_carga(cliente)

    print("\n=== Pipeline completado ===")


if __name__ == "__main__":
    run()
