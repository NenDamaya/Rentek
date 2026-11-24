ALTER TABLE maquinas ADD COLUMN IF NOT EXISTS embedding float8[];

CREATE INDEX IF NOT EXISTS idx_maquinas_nombre_trgm ON maquinas USING gin (nombre gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_maquinas_nombre_comun_trgm ON maquinas USING gin (nombre_comun gin_trgm_ops);
