-- =============================================================
-- Migración: Seguridad - Off-topic tracking y bloqueo de usuarios
-- Agrega columnas para control de mensajes fuera de tema
-- =============================================================

-- 1. Columnas nuevas en chats para tracking de off-topic
ALTER TABLE chats ADD COLUMN IF NOT EXISTS off_topic_strikes INTEGER DEFAULT 0;
ALTER TABLE chats ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';

-- 2. Columnas nuevas en users para bloqueo
ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS blocked_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS closed_chats INTEGER DEFAULT 0;

-- 3. Índices
CREATE INDEX IF NOT EXISTS idx_chats_status ON chats (status);
CREATE INDEX IF NOT EXISTS idx_users_blocked ON users (blocked);

COMMENT ON COLUMN chats.off_topic_strikes IS 'Número de mensajes fuera de tema en este chat (máx 3)';
COMMENT ON COLUMN chats.status IS 'Estado del chat: active, closed_security';
COMMENT ON COLUMN users.blocked IS 'Indica si el usuario está bloqueado por seguridad';
COMMENT ON COLUMN users.closed_chats IS 'Número de chats cerrados por seguridad';
