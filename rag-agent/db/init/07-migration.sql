-- =============================================================
-- Migración: Enriquecimiento de base de datos
-- Agrega columnas estructuradas para pricing, estado y ubicación
-- =============================================================

-- 1. Columnas nuevas en maquinas para pricing estructurado
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS precio_dia NUMERIC(10,2);
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS precio_semana NUMERIC(10,2);
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS precio_mes NUMERIC(10,2);
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS moneda VARCHAR(10) DEFAULT 'MXN';

-- 2. Estado y ubicación de la máquina
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS estado VARCHAR(50) DEFAULT 'disponible';
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS ubicacion VARCHAR(255) DEFAULT '';
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS anio_fabricacion INTEGER;
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS numero_serie VARCHAR(100);

-- 3. Costos adicionales
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS costo_operador_dia NUMERIC(10,2);
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS costo_transporte NUMERIC(10,2);
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS incluye_operador BOOLEAN DEFAULT FALSE;
ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS incluye_transporte BOOLEAN DEFAULT FALSE;

-- 4. Tabla de precios especiales (descuentos por volumen, clientes frecuentes)
CREATE TABLE IF NOT EXISTS precios_especiales (
    id SERIAL PRIMARY KEY,
    maquina_id INTEGER NOT NULL REFERENCES maquinas(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL,  -- 'volumen', 'frecuente', 'promocion', 'temporada'
    min_dias INTEGER,
    max_dias INTEGER,
    descuento_porcentaje NUMERIC(5,2) NOT NULL,
    descripcion TEXT DEFAULT '',
    activo BOOLEAN DEFAULT TRUE,
    fecha_inicio DATE,
    fecha_fin DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_precios_especiales_maquina ON precios_especiales (maquina_id);
CREATE INDEX idx_precios_especiales_tipo ON precios_especiales (tipo);

-- 5. Tabla de sucursales/branches
CREATE TABLE IF NOT EXISTS sucursales (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    direccion TEXT DEFAULT '',
    telefono VARCHAR(50) DEFAULT '',
    email VARCHAR(255) DEFAULT '',
    horario VARCHAR(255) DEFAULT '',
    latitud NUMERIC(10,7),
    longitud NUMERIC(10,7),
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Tabla de inventario por sucursal
CREATE TABLE IF NOT EXISTS inventario_sucursal (
    id SERIAL PRIMARY KEY,
    sucursal_id INTEGER NOT NULL REFERENCES sucursales(id) ON DELETE CASCADE,
    maquina_id INTEGER NOT NULL REFERENCES maquinas(id) ON DELETE CASCADE,
    cantidad_total INTEGER NOT NULL DEFAULT 1,
    cantidad_disponible INTEGER NOT NULL DEFAULT 1,
    cantidad_rentada INTEGER NOT NULL DEFAULT 0,
    cantidad_mantenimiento INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(sucursal_id, maquina_id)
);

CREATE INDEX idx_inventario_sucursal ON inventario_sucursal (sucursal_id);
CREATE INDEX idx_inventario_maquina ON inventario_sucursal (maquina_id);

-- 7. Insertar sucursal por defecto
INSERT INTO sucursales (nombre, direccion, telefono, horario)
VALUES ('Sucursal Principal', 'Av. Industrial #1234, León, Gto.', '477-123-4567', 'Lun-Vie 8:00-18:00, Sáb 8:00-14:00')
ON CONFLICT DO NOTHING;

-- 8. Comentarios en tablas
COMMENT ON COLUMN maquinas.precio_dia IS 'Precio de renta por día en MXN';
COMMENT ON COLUMN maquinas.precio_semana IS 'Precio de renta por semana en MXN';
COMMENT ON COLUMN maquinas.precio_mes IS 'Precio de renta por mes en MXN';
COMMENT ON COLUMN maquinas.estado IS 'disponible, rentada, mantenimiento, inactiva';
COMMENT ON COLUMN maquinas.ubicacion IS 'Sucursal donde se encuentra la máquina';
COMMENT ON COLUMN maquinas.costo_operador_dia IS 'Costo adicional por operador por día';
COMMENT ON COLUMN maquinas.costo_transporte IS 'Costo de transporte hasta la obra';
COMMENT ON TABLE precios_especiales IS 'Descuentos especiales por volumen, clientes frecuentes o promociones';
COMMENT ON TABLE sucursales IS 'Sucursales de la empresa de renta';
COMMENT ON TABLE inventario_sucursal IS 'Inventario de máquinas por sucursal';
