# Schema de Base de Datos — Rentek

**Motor:** PostgreSQL 16  
**Extensiones:** `pg_trgm` (búsqueda fuzzy)

---

## 1. `categorias`

Catálogo de categorías de maquinaria.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Identificador único |
| `nombre` | VARCHAR(255) | NOT NULL, UNIQUE | Nombre de la categoría |
| `descripcion` | TEXT | DEFAULT '' | Descripción de la categoría |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de creación |

**Índices:** `idx_categorias_nombre` en `nombre`

---

## 2. `maquinas`

Fichas técnicas de cada máquina disponible para renta.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Identificador único |
| `categoria_id` | INTEGER | NOT NULL, FK → categorias(id) ON DELETE CASCADE | Categoría padre |
| `nombre` | VARCHAR(255) | NOT NULL | Nombre oficial de la máquina |
| `nombre_comun` | VARCHAR(255) | DEFAULT '' | Nombre coloquial |
| `marcas` | TEXT | DEFAULT '' | Marcas disponibles |
| `modelos_tipicos` | TEXT | DEFAULT '' | Modelos representativos |
| `precio_renta` | VARCHAR(255) | DEFAULT '' | Precio de renta (texto) |
| `sinonimos` | TEXT[] | DEFAULT '{}' | Sinónimos para búsqueda |
| `perfil_cliente` | TEXT | DEFAULT '' | Cliente ideal |
| `especificaciones` | JSONB | DEFAULT '{}' | Specs técnicas (peso, potencia, etc.) |
| `recomendado` | TEXT[] | DEFAULT '{}' | Casos donde SÍ se recomienda |
| `no_recomendado` | TEXT[] | DEFAULT '{}' | Casos donde NO se recomienda |
| `casos_uso` | TEXT[] | DEFAULT '{}' | Casos de uso específicos |
| `preguntas_frecuentes` | JSONB | DEFAULT '[]' | FAQ en formato JSON |
| `reglas_negocio` | TEXT[] | DEFAULT '{}' | Reglas de renta, descuentos, etc. |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de creación |

**Índices:**
- `idx_maquinas_nombre` en `nombre`
- `idx_maquinas_categoria` en `categoria_id`
- `idx_maquinas_trgm` GIN en `nombre` (búsqueda fuzzy)

---

## 3. `proyectos`

Combinaciones típicas de maquinaria por tipo de proyecto.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Identificador único |
| `nombre` | VARCHAR(255) | NOT NULL, UNIQUE | Nombre del proyecto |
| `maquinarias` | TEXT[] | DEFAULT '{}' | Lista de máquinas requeridas |
| `consideraciones` | TEXT | DEFAULT '' | Notas técnicas del proyecto |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de creación |

**Índices:** `idx_proyectos_nombre` en `nombre`

---

## 4. `disponibilidad`

Calendario de disponibilidad por máquina y fecha.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Identificador único |
| `maquina_id` | INTEGER | NOT NULL, FK → maquinas(id) ON DELETE CASCADE | Máquina |
| `fecha` | DATE | NOT NULL | Fecha del calendario |
| `disponible` | BOOLEAN | NOT NULL, DEFAULT TRUE | `true` = disponible |
| `notas` | TEXT | DEFAULT '' | Notas (ej: "en mantenimiento") |

**Constraints:** UNIQUE(`maquina_id`, `fecha`)  
**Índices:**
- `idx_disponibilidad_maquina_fecha` en (`maquina_id`, `fecha`)
- `idx_disponibilidad_fecha` en `fecha`

---

## 5. `solicitudes_renta`

Solicitudes formales de renta registradas por el asistente.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Identificador único |
| `folio` | VARCHAR(20) | NOT NULL, UNIQUE | Folio único (ej: SOL-20260720-001) |
| `cliente` | VARCHAR(255) | NOT NULL | Nombre del cliente/empresa |
| `contacto` | VARCHAR(255) | NOT NULL | Teléfono o email |
| `maquinas` | JSONB | NOT NULL | Lista de máquinas `[{"nombre": "...", "cantidad": 1}]` |
| `fecha_inicio` | DATE | NOT NULL | Fecha de inicio |
| `fecha_fin` | DATE | NOT NULL | Fecha de fin |
| `estado` | VARCHAR(50) | NOT NULL, DEFAULT 'pendiente' | `pendiente` / `confirmada` / `cancelada` |
| `notas` | TEXT | DEFAULT '' | Notas adicionales |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de registro |

**Índices:**
- `idx_solicitudes_estado` en `estado`
- `idx_solicitudes_fechas` en (`fecha_inicio`, `fecha_fin`)

---

## 6. `cotizaciones`

Cotizaciones formales generadas con folio y cálculo de costos.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Identificador único |
| `folio` | VARCHAR(20) | NOT NULL, UNIQUE | Folio único (ej: COT-20260720-001) |
| `cliente` | VARCHAR(255) | NOT NULL | Nombre del cliente/empresa |
| `contacto` | VARCHAR(255) | NOT NULL | Teléfono o email |
| `maquinas` | JSONB | NOT NULL | Lista de máquinas |
| `dias` | INTEGER | NOT NULL | Días de renta |
| `subtotal` | NUMERIC(12,2) | NOT NULL | Subtotal antes de descuento |
| `descuento` | NUMERIC(12,2) | DEFAULT 0 | Descuento aplicado |
| `total` | NUMERIC(12,2) | NOT NULL | Total a pagar |
| `valida_hasta` | DATE | NOT NULL | Vigencia (30 días) |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de creación |

**Índices:** `idx_cotizaciones_folio` en `folio`

---

## 7. `observability_logs`

Logs de cada interacción con el asistente para métricas y debugging.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Identificador único |
| `session_id` | VARCHAR(36) | | UUID de la sesión |
| `timestamp` | TIMESTAMP | DEFAULT NOW() | Momento de la interacción |
| `user_prompt` | TEXT | NOT NULL | Pregunta del usuario |
| `system_response` | TEXT | | Respuesta del asistente |
| `ttft_ms` | FLOAT | | Time to first token (ms) |
| `total_latency_ms` | FLOAT | | Latencia total (ms) |
| `tokens_per_second` | FLOAT | | Velocidad de generación |
| `was_blocked` | BOOLEAN | DEFAULT FALSE | Si fue bloqueado por guardrails |
| `block_reason` | VARCHAR(255) | | Razón del bloqueo |
| `tools_executed` | JSONB | DEFAULT '[]' | Herramientas ejecutadas |
| `model_used` | VARCHAR(100) | | Modelo utilizado |
| `tokens_input` | INTEGER | | Tokens de entrada |
| `tokens_output` | INTEGER | | Tokens de salida |

**Índices:**
- `idx_observability_session` en `session_id`
- `idx_observability_timestamp` en `timestamp`
- `idx_observability_blocked` en `was_blocked`

---

## 8. `conversations`

Sesiones de conversación (agrupan mensajes).

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID de la conversación |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Última actualización |
| `metadata` | JSONB | DEFAULT '{}' | Datos adicionales |
| `user_id` | INTEGER | FK → users(id) ON DELETE SET NULL | Usuario dueño |
| `chat_id` | VARCHAR(36) | FK → chats(id) ON DELETE SET NULL | Chat asociado |

**Índices:**
- `idx_conversations_updated` en `updated_at`
- `idx_conversations_chat` en `chat_id`

---

## 9. `conversation_messages`

Mensajes individuales dentro de una conversación.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Identificador único |
| `conversation_id` | VARCHAR(36) | NOT NULL, FK → conversations(id) ON DELETE CASCADE | Conversación padre |
| `role` | VARCHAR(20) | NOT NULL, CHECK IN ('system', 'user', 'assistant', 'tool') | Rol del mensaje |
| `content` | TEXT | | Contenido del mensaje |
| `tool_calls` | JSONB | | Llamadas a herramientas (JSON) |
| `tool_call_id` | VARCHAR(100) | | ID de la llamada a herramienta |
| `tool_name` | VARCHAR(100) | | Nombre de la herramienta |
| `tokens_estimated` | INTEGER | DEFAULT 0 | Tokens estimados |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha del mensaje |

**Índices:** `idx_messages_conversation` en (`conversation_id`, `created_at`)

---

## 10. `users`

Usuarios registrados del sistema.

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | SERIAL | PRIMARY KEY | Identificador único |
| `username` | VARCHAR(100) | NOT NULL, UNIQUE | Nombre de usuario |
| `email` | VARCHAR(255) | DEFAULT '' | Email |
| `password_hash` | VARCHAR(255) | DEFAULT '' | Hash de contraseña (PBKDF2) |
| `display_name` | VARCHAR(255) | DEFAULT '' | Nombre para mostrar |
| `role` | VARCHAR(20) | DEFAULT 'user', CHECK IN ('admin', 'user') | Rol |
| `provider` | VARCHAR(50) | DEFAULT 'local' | Proveedor OAuth (google/local) |
| `provider_id` | VARCHAR(255) | DEFAULT '' | ID en el proveedor |
| `avatar_url` | TEXT | DEFAULT '' | URL del avatar |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de registro |
| `last_login` | TIMESTAMP | | Último acceso |

**Índices:**
- `idx_users_username` en `username`
- `idx_users_email` en `email`
- `idx_users_provider` en (`provider`, `provider_id`)

---

## 11. `chats`

Chats múltiples por usuario (sidebar).

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID del chat |
| `user_id` | INTEGER | NOT NULL, FK → users(id) ON DELETE CASCADE | Usuario dueño |
| `title` | VARCHAR(255) | DEFAULT 'Nuevo chat' | Título del chat |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Última actualización |

**Índices:** `idx_chats_user` en (`user_id`, `updated_at DESC`)

---

## Relaciones

```
users (1) ──── (N) chats
  │                 │
  │                 └── (1) ──── (N) conversations
  │                                   │
  └── (1) ──── (N) conversations      │
                                       └── (1) ──── (N) conversation_messages

categorias (1) ──── (N) maquinas
maquinas (1) ──── (N) disponibilidad
```

---

## Archivos SQL

| Archivo | Contenido |
|---------|-----------|
| `db/init/01-schema.sql` | categorias, maquinas, proyectos |
| `db/init/02-business.sql` | disponibilidad, solicitudes_renta, cotizaciones |
| `db/init/03-observability.sql` | observability_logs |
| `db/init/04-sessions.sql` | conversations, conversation_messages |
| `db/init/05-users.sql` | users |
| `db/init/06-chats.sql` | chats + ALTER TABLE conversations |
