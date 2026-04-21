USE copperprint_oltp;
GO

IF OBJECT_ID('cp.fact_produccion_empresa', 'U') IS NOT NULL DROP TABLE cp.fact_produccion_empresa;
IF OBJECT_ID('cp.fact_consumo_agua', 'U') IS NOT NULL DROP TABLE cp.fact_consumo_agua;
IF OBJECT_ID('cp.dim_empresa',  'U') IS NOT NULL DROP TABLE cp.dim_empresa;
IF OBJECT_ID('cp.dim_proceso',  'U') IS NOT NULL DROP TABLE cp.dim_proceso;
IF OBJECT_ID('cp.dim_fuente',   'U') IS NOT NULL DROP TABLE cp.dim_fuente;
IF OBJECT_ID('cp.dim_region',   'U') IS NOT NULL DROP TABLE cp.dim_region;
IF OBJECT_ID('cp.dim_tiempo',   'U') IS NOT NULL DROP TABLE cp.dim_tiempo;
GO

CREATE TABLE cp.dim_tiempo (
    id_tiempo   INT          NOT NULL PRIMARY KEY,
    anio        SMALLINT     NOT NULL,
    mes         TINYINT      NULL,
    trimestre   TINYINT      NULL,
    es_anual    BIT          NOT NULL DEFAULT 1
);
GO

CREATE TABLE cp.dim_region (
    id_region       INT               NOT NULL PRIMARY KEY,
    codigo_region   VARCHAR(5)        NOT NULL,
    nombre_region   VARCHAR(80)       NOT NULL,
    zona            VARCHAR(20)       NULL
);
GO

CREATE TABLE cp.dim_fuente (
    id_fuente       INT               NOT NULL PRIMARY KEY,
    nombre_fuente   VARCHAR(80)       NOT NULL,
    categoria       VARCHAR(40)       NOT NULL,
    es_recirculada  BIT               NOT NULL DEFAULT 0
);
GO

CREATE TABLE cp.dim_proceso (
    id_proceso      INT               NOT NULL PRIMARY KEY,
    nombre_proceso  VARCHAR(80)       NOT NULL,
    etapa           VARCHAR(40)       NULL
);
GO

CREATE TABLE cp.dim_empresa (
    id_empresa          INT               NOT NULL PRIMARY KEY,
    nombre_empresa      VARCHAR(120)      NOT NULL,
    grupo_controlador   VARCHAR(80)       NULL,
    tipo                VARCHAR(20)       NULL,
    region_principal    VARCHAR(80)       NULL
);
GO

CREATE TABLE cp.fact_consumo_agua (
    id_consumo       BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    id_tiempo        INT            NOT NULL REFERENCES cp.dim_tiempo(id_tiempo),
    id_fuente        INT            NOT NULL REFERENCES cp.dim_fuente(id_fuente),
    id_region        INT            NULL     REFERENCES cp.dim_region(id_region),
    id_proceso       INT            NULL     REFERENCES cp.dim_proceso(id_proceso),
    caudal_ls        DECIMAL(18,4)  NOT NULL,
    volumen_m3_anual DECIMAL(18,2)  NOT NULL,
    es_proyeccion    BIT            NOT NULL DEFAULT 0,
    fuente_dato      VARCHAR(50)    NOT NULL DEFAULT 'COCHILCO'
);
GO

CREATE TABLE cp.fact_produccion_empresa (
    id_produccion       BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    id_tiempo           INT          NOT NULL REFERENCES cp.dim_tiempo(id_tiempo),
    id_empresa          INT          NOT NULL REFERENCES cp.dim_empresa(id_empresa),
    miles_tm_cu_fino    DECIMAL(10,2) NOT NULL,
    es_anual            BIT          NOT NULL DEFAULT 1
);
GO

CREATE INDEX ix_fca_tiempo   ON cp.fact_consumo_agua(id_tiempo);
CREATE INDEX ix_fca_fuente   ON cp.fact_consumo_agua(id_fuente);
CREATE INDEX ix_fca_region   ON cp.fact_consumo_agua(id_region);
CREATE INDEX ix_fpe_tiempo   ON cp.fact_produccion_empresa(id_tiempo);
CREATE INDEX ix_fpe_empresa  ON cp.fact_produccion_empresa(id_empresa);
GO
