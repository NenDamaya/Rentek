CREATE TABLE IF NOT EXISTS disponibilidad (
    id SERIAL PRIMARY KEY,
    maquina_id INTEGER NOT NULL REFERENCES maquinas(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    disponible BOOLEAN NOT NULL DEFAULT TRUE,
    notas TEXT DEFAULT '',
    UNIQUE(maquina_id, fecha)
);

CREATE INDEX idx_disponibilidad_maquina_fecha ON disponibilidad (maquina_id, fecha);
CREATE INDEX idx_disponibilidad_fecha ON disponibilidad (fecha);

CREATE TABLE IF NOT EXISTS solicitudes_renta (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(20) NOT NULL UNIQUE,
    cliente VARCHAR(255) NOT NULL,
    contacto VARCHAR(255) NOT NULL,
    maquinas JSONB NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'pendiente',
    notas TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_solicitudes_estado ON solicitudes_renta (estado);
CREATE INDEX idx_solicitudes_fechas ON solicitudes_renta (fecha_inicio, fecha_fin);

CREATE TABLE IF NOT EXISTS cotizaciones (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(20) NOT NULL UNIQUE,
    cliente VARCHAR(255) NOT NULL,
    contacto VARCHAR(255) NOT NULL,
    maquinas JSONB NOT NULL,
    dias INTEGER NOT NULL,
    subtotal NUMERIC(12, 2) NOT NULL,
    descuento NUMERIC(12, 2) DEFAULT 0,
    total NUMERIC(12, 2) NOT NULL,
    valida_hasta DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cotizaciones_folio ON cotizaciones (folio);
