-- =============================================================
-- Tabla de Chats: Historial múltiple por usuario
-- =============================================================

CREATE TABLE IF NOT EXISTS chats (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'Nuevo chat',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chats_user ON chats (user_id, updated_at DESC);

-- Vincular conversaciones existentes con usuario (si aplica)
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS chat_id VARCHAR(36) REFERENCES chats(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_conversations_chat ON conversations (chat_id);
