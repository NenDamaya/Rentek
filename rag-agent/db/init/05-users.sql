-- =============================================================
-- Tabla de Usuarios: Autenticación + OAuth
-- =============================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) DEFAULT '',
    password_hash VARCHAR(255) DEFAULT '',
    display_name VARCHAR(255) DEFAULT '',
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    provider VARCHAR(50) DEFAULT 'local',
    provider_id VARCHAR(255) DEFAULT '',
    avatar_url TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_provider ON users (provider, provider_id);
