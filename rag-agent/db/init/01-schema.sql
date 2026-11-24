-- =============================================================
-- Esquema de Base de Datos: Maquinaria Pesada - Renta
-- Motor: PostgreSQL 16
-- =============================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------------------------------------------------------
-- 1. CATEGORÍAS
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(255) NOT NULL UNIQUE,
    descripcion TEXT DEFAULT '',
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_categorias_nombre ON categorias (nombre);

-- ---------------------------------------------------------
-- 2. MAQUINAS
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS maquinas (
    id                SERIAL PRIMARY KEY,
    categoria_id      INTEGER NOT NULL REFERENCES categorias(id) ON DELETE CASCADE,
    nombre            VARCHAR(255) NOT NULL,
    nombre_comun      VARCHAR(255) DEFAULT '',
    marcas            TEXT DEFAULT '',
    modelos_tipicos   TEXT DEFAULT '',
    precio_renta      VARCHAR(255) DEFAULT '',
    sinonimos         TEXT[] DEFAULT '{}',
    perfil_cliente    TEXT DEFAULT '',
    especificaciones  JSONB DEFAULT '{}',
    recomendado       TEXT[] DEFAULT '{}',
    no_recomendado    TEXT[] DEFAULT '{}',
    casos_uso         TEXT[] DEFAULT '{}',
    preguntas_frecuentes JSONB DEFAULT '[]',
    reglas_negocio    TEXT[] DEFAULT '{}',
    created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_maquinas_nombre     ON maquinas (nombre);
CREATE INDEX idx_maquinas_categoria  ON maquinas (categoria_id);
CREATE INDEX idx_maquinas_trgm ON maquinas USING GIN (nombre gin_trgm_ops);

-- ---------------------------------------------------------
-- 3. PROYECTOS
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS proyectos (
    id                SERIAL PRIMARY KEY,
    nombre            VARCHAR(255) NOT NULL UNIQUE,
    maquinarias       TEXT[] DEFAULT '{}',
    consideraciones   TEXT DEFAULT '',
    created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_proyectos_nombre ON proyectos (nombre);
