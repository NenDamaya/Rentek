CREATE TABLE IF NOT EXISTS carrito_items (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    maquina_nombre VARCHAR(255) NOT NULL,
    maquina_json JSONB NOT NULL,
    duration INTEGER NOT NULL DEFAULT 1,
    duration_unit VARCHAR(20) NOT NULL DEFAULT 'dias',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    precio_dia NUMERIC(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_carrito_user_id ON carrito_items(user_id);
