-- =============================================================
-- Tabla de Observabilidad: Logs de interacciones
-- =============================================================

CREATE TABLE IF NOT EXISTS observability_logs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36),
    timestamp TIMESTAMP DEFAULT NOW(),
    user_prompt TEXT NOT NULL,
    system_response TEXT,
    ttft_ms FLOAT,
    total_latency_ms FLOAT,
    tokens_per_second FLOAT,
    was_blocked BOOLEAN DEFAULT FALSE,
    block_reason VARCHAR(255),
    tools_executed JSONB DEFAULT '[]',
    model_used VARCHAR(100),
    tokens_input INTEGER,
    tokens_output INTEGER
);

CREATE INDEX idx_observability_session ON observability_logs (session_id);
CREATE INDEX idx_observability_timestamp ON observability_logs (timestamp);
CREATE INDEX idx_observability_blocked ON observability_logs (was_blocked);
