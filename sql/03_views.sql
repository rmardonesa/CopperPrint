USE copperprint_oltp;
GO

IF OBJECT_ID('cp.vw_consumo_anual_fuente',       'V') IS NOT NULL DROP VIEW cp.vw_consumo_anual_fuente;
IF OBJECT_ID('cp.vw_extraccion_regional',         'V') IS NOT NULL DROP VIEW cp.vw_extraccion_regional;
IF OBJECT_ID('cp.vw_consumo_por_proceso',         'V') IS NOT NULL DROP VIEW cp.vw_consumo_por_proceso;
IF OBJECT_ID('cp.vw_produccion_empresa_anual',    'V') IS NOT NULL DROP VIEW cp.vw_produccion_empresa_anual;
IF OBJECT_ID('cp.vw_proyeccion_demanda',          'V') IS NOT NULL DROP VIEW cp.vw_proyeccion_demanda;
IF OBJECT_ID('cp.vw_intensidad_hidrica',          'V') IS NOT NULL DROP VIEW cp.vw_intensidad_hidrica;
GO

CREATE VIEW cp.vw_consumo_anual_fuente AS
SELECT
    t.anio,
    f.nombre_fuente,
    f.categoria,
    f.es_recirculada,
    SUM(c.volumen_m3_anual)   AS volumen_m3_anual,
    SUM(c.caudal_ls)          AS caudal_ls_total
FROM cp.fact_consumo_agua c
JOIN cp.dim_tiempo t  ON c.id_tiempo = t.id_tiempo
JOIN cp.dim_fuente f  ON c.id_fuente = f.id_fuente
WHERE t.es_anual = 1
  AND c.id_region  IS NULL
  AND c.id_proceso IS NULL
  AND c.es_proyeccion = 0
GROUP BY t.anio, f.nombre_fuente, f.categoria, f.es_recirculada;
GO

CREATE VIEW cp.vw_extraccion_regional AS
SELECT
    t.anio,
    r.nombre_region,
    r.zona,
    f.categoria                AS tipo_fuente,
    SUM(c.volumen_m3_anual)    AS volumen_m3_anual,
    SUM(c.caudal_ls)           AS caudal_ls_total
FROM cp.fact_consumo_agua c
JOIN cp.dim_tiempo  t ON c.id_tiempo  = t.id_tiempo
JOIN cp.dim_region  r ON c.id_region  = r.id_region
JOIN cp.dim_fuente  f ON c.id_fuente  = f.id_fuente
WHERE t.es_anual = 1
  AND c.es_proyeccion = 0
GROUP BY t.anio, r.nombre_region, r.zona, f.categoria;
GO

CREATE VIEW cp.vw_consumo_por_proceso AS
SELECT
    t.anio,
    p.nombre_proceso,
    p.etapa,
    SUM(c.volumen_m3_anual)    AS volumen_m3_anual,
    SUM(c.caudal_ls)           AS caudal_ls_total
FROM cp.fact_consumo_agua c
JOIN cp.dim_tiempo  t ON c.id_tiempo  = t.id_tiempo
JOIN cp.dim_proceso p ON c.id_proceso = p.id_proceso
WHERE t.es_anual = 1
  AND c.es_proyeccion = 0
GROUP BY t.anio, p.nombre_proceso, p.etapa;
GO

CREATE VIEW cp.vw_produccion_empresa_anual AS
SELECT
    t.anio,
    e.nombre_empresa,
    e.grupo_controlador,
    e.tipo,
    SUM(p.miles_tm_cu_fino)    AS miles_tm_cu_fino
FROM cp.fact_produccion_empresa p
JOIN cp.dim_tiempo  t ON p.id_tiempo  = t.id_tiempo
JOIN cp.dim_empresa e ON p.id_empresa = e.id_empresa
WHERE p.es_anual = 1
GROUP BY t.anio, e.nombre_empresa, e.grupo_controlador, e.tipo;
GO


CREATE VIEW cp.vw_proyeccion_demanda AS
SELECT
    t.anio,
    f.nombre_fuente,
    f.categoria,
    SUM(c.volumen_m3_anual)    AS volumen_m3_anual_proyectado,
    SUM(c.caudal_ls)           AS caudal_ls_proyectado
FROM cp.fact_consumo_agua c
JOIN cp.dim_tiempo t ON c.id_tiempo = t.id_tiempo
JOIN cp.dim_fuente f ON c.id_fuente = f.id_fuente
WHERE c.es_proyeccion = 1
  AND t.es_anual = 1
GROUP BY t.anio, f.nombre_fuente, f.categoria;
GO

CREATE VIEW cp.vw_intensidad_hidrica AS
SELECT
    t.anio,
    SUM(c.volumen_m3_anual)                             AS agua_total_m3,
    SUM(p.miles_tm_cu_fino) * 1000                      AS produccion_tm_cu,
    CASE
        WHEN SUM(p.miles_tm_cu_fino) > 0
        THEN SUM(c.volumen_m3_anual) / (SUM(p.miles_tm_cu_fino) * 1000)
    END                                                 AS m3_por_tm_cu
FROM cp.dim_tiempo t
LEFT JOIN cp.fact_consumo_agua c
       ON c.id_tiempo   = t.id_tiempo
      AND c.es_proyeccion = 0
      AND c.id_region   IS NULL
      AND c.id_proceso  IS NULL
LEFT JOIN cp.fact_produccion_empresa p
       ON p.id_tiempo   = t.id_tiempo
      AND p.es_anual    = 1
WHERE t.es_anual = 1
GROUP BY t.anio
HAVING SUM(c.volumen_m3_anual) IS NOT NULL
   AND SUM(p.miles_tm_cu_fino) IS NOT NULL;
GO
