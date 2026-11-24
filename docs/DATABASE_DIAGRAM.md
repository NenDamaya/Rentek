# Diagrama de Base de Datos - Rentek

## Esquema Completo (PostgreSQL)

```mermaid
erDiagram
    %% ==================== USUARIOS Y AUTENTICACIÓN ====================
    USERS {
        int id PK "SERIAL PRIMARY KEY"
        varchar username UK "NOT NULL UNIQUE"
        varchar email "DEFAULT ''"
        varchar password_hash "DEFAULT '' SELECT: false"
        varchar display_name "DEFAULT ''"
        varchar role "DEFAULT 'user' CHECK (admin|user)"
        varchar provider "DEFAULT 'local'"
        varchar provider_id "DEFAULT ''"
        text avatar_url "DEFAULT ''"
        boolean blocked "DEFAULT false"
        timestamp blocked_at "NULLABLE"
        int closed_chats "DEFAULT 0"
        timestamp created_at "DEFAULT NOW()"
        timestamp last_login "NULLABLE"
    }

    %% ==================== CATÁLOGO DE MAQUINARIA ====================
    CATEGORIAS {
        int id PK "SERIAL PRIMARY KEY"
        varchar nombre UK "NOT NULL UNIQUE"
        text descripcion "DEFAULT ''"
        timestamp created_at "DEFAULT NOW()"
    }

    MAQUINAS {
        int id PK "SERIAL PRIMARY KEY"
        varchar nombre "NOT NULL"
        varchar nombre_comun "DEFAULT ''"
        text marcas "DEFAULT ''"
        text modelos_tipicos "DEFAULT ''"
        varchar precio_renta "DEFAULT ''"
        text[] sinonimos "DEFAULT '{}'"
        text perfil_cliente "DEFAULT ''"
        jsonb especificaciones "DEFAULT '{}'"
        text[] recomendado "DEFAULT '{}'"
        text[] no_recomendado "DEFAULT '{}'"
        text[] casos_uso "DEFAULT '{}'"
        jsonb preguntas_frecuentes "DEFAULT '[]'"
        text[] reglas_negocio "DEFAULT '{}'"
        %% Precios estructurados (migración 07)
        numeric precio_dia "NULLABLE"
        numeric precio_semana "NULLABLE"
        numeric precio_mes "NULLABLE"
        varchar moneda "DEFAULT 'MXN'"
        varchar estado "DEFAULT 'disponible'"
        varchar ubicacion "DEFAULT ''"
        int anio_fabricacion "NULLABLE"
        varchar numero_serie "NULLABLE"
        numeric costo_operador_dia "NULLABLE"
        numeric costo_transporte "NULLABLE"
        boolean incluye_operador "DEFAULT false"
        boolean incluye_transporte "DEFAULT false"
        timestamp created_at "DEFAULT NOW()"
        int categoria_id FK "REFERENCES categorias(id) ON DELETE CASCADE"
    }

    PROYECTOS {
        int id PK "SERIAL PRIMARY KEY"
        varchar nombre UK "NOT NULL UNIQUE"
        text[] maquinarias "DEFAULT '{}'"
        text consideraciones "DEFAULT ''"
        timestamp created_at "DEFAULT NOW()"
    }

    %% ==================== DISPONIBILIDAD E INVENTARIO ====================
    DISPONIBILIDAD {
        int id PK "SERIAL PRIMARY KEY"
        int maquina_id FK "REFERENCES maquinas(id) ON DELETE CASCADE"
        date fecha "NOT NULL"
        boolean disponible "DEFAULT true"
        text notas "DEFAULT ''"
        UNIQUE(maquina_id, fecha)
    }

    SUCURSALES {
        int id PK "SERIAL PRIMARY KEY"
        varchar nombre "NOT NULL"
        text direccion "DEFAULT ''"
        varchar telefono "DEFAULT ''"
        varchar email "DEFAULT ''"
        varchar horario "DEFAULT ''"
        numeric latitud "NULLABLE"
        numeric longitud "NULLABLE"
        boolean activa "DEFAULT true"
        timestamp created_at "DEFAULT NOW()"
    }

    INVENTARIO_SUCURSAL {
        int id PK "SERIAL PRIMARY KEY"
        int sucursal_id FK "REFERENCES sucursales(id) ON DELETE CASCADE"
        int maquina_id FK "REFERENCES maquinas(id) ON DELETE CASCADE"
        int cantidad_total "DEFAULT 1"
        int cantidad_disponible "DEFAULT 1"
        int cantidad_rentada "DEFAULT 0"
        int cantidad_mantenimiento "DEFAULT 0"
        timestamp created_at "DEFAULT NOW()"
        UNIQUE(sucursal_id, maquina_id)
    }

    PRECIOS_ESPECIALES {
        int id PK "SERIAL PRIMARY KEY"
        int maquina_id FK "REFERENCES maquinas(id) ON DELETE CASCADE"
        varchar tipo "NOT NULL (volumen|frecuente|promocion|temporada)"
        int min_dias "NULLABLE"
        int max_dias "NULLABLE"
        numeric descuento_porcentaje "NOT NULL"
        text descripcion "DEFAULT ''"
        boolean activo "DEFAULT true"
        date fecha_inicio "NULLABLE"
        date fecha_fin "NULLABLE"
        timestamp created_at "DEFAULT NOW()"
    }

    %% ==================== NEGOCIO: SOLICITUDES Y COTIZACIONES ====================
    SOLICITUDES_RENTA {
        int id PK "SERIAL PRIMARY KEY"
        varchar folio UK "NOT NULL UNIQUE (SOL-YYYY-XXXXXX)"
        varchar cliente "NOT NULL"
        varchar contacto "NOT NULL"
        jsonb maquinas "NOT NULL"
        date fecha_inicio "NOT NULL"
        date fecha_fin "NOT NULL"
        varchar estado "DEFAULT 'pendiente' (pendiente|confirmada|cancelada|completada)"
        text notas "DEFAULT ''"
        int user_id FK "NULLABLE REFERENCES users(id) ON DELETE SET NULL"
        timestamp created_at "DEFAULT NOW()"
    }

    COTIZACIONES {
        int id PK "SERIAL PRIMARY KEY"
        varchar folio UK "NOT NULL UNIQUE (COT-YYYY-XXXXXX)"
        varchar cliente "NOT NULL"
        varchar contacto "NOT NULL"
        jsonb maquinas "NOT NULL"
        int dias "NOT NULL"
        numeric subtotal "NOT NULL"
        numeric descuento "DEFAULT 0"
        numeric total "NOT NULL"
        date valida_hasta "NOT NULL"
        int user_id FK "NULLABLE REFERENCES users(id) ON DELETE SET NULL"
        timestamp created_at "DEFAULT NOW()"
    }

    %% ==================== CARRITO DE COMPRAS ====================
    CARRITO_ITEMS {
        int id PK "SERIAL PRIMARY KEY"
        int user_id FK "REFERENCES users(id) ON DELETE CASCADE"
        varchar maquina_nombre "NOT NULL"
        jsonb maquina_json "NOT NULL"
        int duration "DEFAULT 1"
        varchar duration_unit "DEFAULT 'dias'"
        date start_date "NOT NULL"
        date end_date "NOT NULL"
        numeric precio_dia "DEFAULT 0"
        timestamp created_at "DEFAULT NOW()"
    }

    %% ==================== CHATS Y CONVERSACIONES ====================
    CHATS {
        uuid id PK "PRIMARY KEY"
        int user_id FK "REFERENCES users(id) ON DELETE CASCADE"
        varchar title "DEFAULT 'Nuevo chat'"
        varchar status "DEFAULT 'active' (active|closed_security)"
        int off_topic_strikes "DEFAULT 0"
        timestamp created_at "DEFAULT NOW()"
        timestamp updated_at "DEFAULT NOW()"
    }

    CONVERSATIONS {
        uuid id PK "PRIMARY KEY"
        varchar chat_id FK "REFERENCES chats(id) ON DELETE CASCADE"
        int user_id FK "NULLABLE REFERENCES users(id) ON DELETE SET NULL"
        timestamp created_at "DEFAULT NOW()"
    }

    CONVERSATION_MESSAGES {
        int id PK "SERIAL PRIMARY KEY"
        uuid conversation_id FK "REFERENCES conversations(id) ON DELETE CASCADE"
        varchar role "NOT NULL (user|assistant|system|tool)"
        text content "NULLABLE"
        jsonb tool_calls "NULLABLE"
        varchar tool_call_id "NULLABLE"
        varchar name "NULLABLE"
        timestamp created_at "DEFAULT NOW()"
    }

    %% ==================== RELACIONES ====================
    USERS ||--o{ CHATS : "1:N"
    USERS ||--o{ SOLICITUDES_RENTA : "1:N"
    USERS ||--o{ COTIZACIONES : "1:N"
    USERS ||--o{ CARRITO_ITEMS : "1:N"

    CATEGORIAS ||--o{ MAQUINAS : "1:N"

    MAQUINAS ||--o{ DISPONIBILIDAD : "1:N"
    MAQUINAS ||--o{ INVENTARIO_SUCURSAL : "1:N"
    MAQUINAS ||--o{ PRECIOS_ESPECIALES : "1:N"

    SUCURSALES ||--o{ INVENTARIO_SUCURSAL : "1:N"

    CHATS ||--o{ CONVERSATIONS : "1:N"
    CONVERSATIONS ||--o{ CONVERSATION_MESSAGES : "1:N"
```

---

## Índices Principales

| Tabla | Índices |
|-------|---------|
| **users** | `username` (UNIQUE), `email`, `provider+provider_id`, `blocked` |
| **categorias** | `nombre` (UNIQUE) |
| **maquinas** | `nombre`, `categoria_id`, `nombre` (GIN trigram) |
| **disponibilidad** | `maquina_id+fecha` (UNIQUE), `fecha` |
| **solicitudes_renta** | `estado`, `fecha_inicio+fecha_fin`, `user_id` |
| **cotizaciones** | `folio` (UNIQUE), `user_id` |
| **carrito_items** | `user_id` |
| **chats** | `user_id+updatedAt`, `status` |
| **conversations** | `chat_id`, `user_id` |
| **conversation_messages** | `conversation_id+createdAt` |
| **inventario_sucursal** | `sucursal_id`, `maquina_id`, `sucursal_id+maquina_id` (UNIQUE) |
| **precios_especiales** | `maquina_id`, `tipo` |

---

## Datos de Ejemplo (Catálogo)

### Categorías principales
- **Excavadoras** - Excavadora Hidráulica de Orugas
- **Bulldozers** - Bulldozer de Orugas, Motoniveladora Articulada
- **Retroexcavadoras** - Retroexcavadora Mixta 4x4
- **Grúas** - Grúa Telescópica Móvil
- **Compactadores** - Rodillo Compactador Vibratorio
- **Generadores** - Planta de Luz / Generador Diesel
- **Minicargadores** - Minicargador Compacto (Bobcat)

### Proyectos predefinidos
- Construcción de vivienda
- Movimiento de tierra
- Pavimentación
- Excavación de cimentación
- Demolición
- Minería
- Ampliación en segundo piso

---

## Flujo de Datos Típico

```
1. Usuario se registra/loguea (USERS)
        │
        ▼
2. Navega catálogo (CATEGORIAS → MAQUINAS)
        │
        ▼
3. Agrega al carrito (CARRITO_ITEMS)
        │
        ▼
4. Calcula cotización (COTIZACIONES) o Checkout directo
        │
        ├──→ Cotización formal → COTIZACIONES
        │
        └──→ Checkout carrito → SOLICITUDES_RENTA
                │
                ▼
         Chat con asesor IA (CHATS → CONVERSATIONS → CONVERSATION_MESSAGES)
                │
                ▼
         Confirma solicitud → SOLICITUDES_RENTA (estado: confirmada)
```

---

## Migraciones SQL (orden de ejecución)

```bash
01-schema.sql           # Tablas base: categorias, maquinas, proyectos
02-business.sql         # Negocio: disponibilidad, solicitudes_renta, cotizaciones
03-observability.sql    # Logs de observabilidad
04-sessions.sql         # Sesiones (legacy)
05-users.sql            # Usuarios y autenticación
06-chats.sql            # Chats, conversations, messages
07-migration.sql        # Enriquecimiento: precios, estado, sucursales, inventario
08-security.sql         # Seguridad: off_topic_strikes, blocked users
09-user-foreign-keys.sql # FK user_id en solicitudes y cotizaciones
10-embeddings.sql       # Tabla para embeddings vectoriales (ChromaDB sync)
10-cliente-role.sql     # Role cliente
11-carrito.sql          # Carrito de compras
```

---

## Consultas Útiles

### Ver todas las máquinas con su categoría
```sql
SELECT m.nombre, m.precio_renta, c.nombre as categoria
FROM maquinas m
JOIN categorias c ON m.categoria_id = c.id
ORDER BY c.nombre, m.nombre;
```

### Disponibilidad de una máquina en rango
```sql
SELECT fecha, disponible, notas
FROM disponibilidad
WHERE maquina_id = 1
  AND fecha BETWEEN '2026-01-15' AND '2026-01-20'
ORDER BY fecha;
```

### Inventario por sucursal
```sql
SELECT s.nombre as sucursal, m.nombre as maquina,
       i.cantidad_total, i.cantidad_disponible, i.cantidad_rentada
FROM inventario_sucursal i
JOIN sucursales s ON i.sucursal_id = s.id
JOIN maquinas m ON i.maquina_id = m.id
WHERE s.activa = true
ORDER BY s.nombre, m.nombre;
```

### Historial de chat de un usuario
```sql
SELECT c.id, c.title, c.created_at, c.status,
       cm.role, cm.content, cm.created_at as msg_time
FROM chats c
JOIN conversations conv ON conv.chat_id = c.id
JOIN conversation_messages cm ON cm.conversation_id = conv.id
WHERE c.user_id = 1
ORDER BY c.updated_at DESC, cm.created_at ASC;
```