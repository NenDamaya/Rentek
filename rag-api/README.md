# Rentek API (NestJS)

API REST para renta de maquinaria pesada. Habla con el servicio `rag-agent` (FastAPI) para IA/RAG y con el frontend Svelte.

## Arquitectura Híbrida

| Componente | Tecnología | Responsabilidad |
|------------|-----------|-----------------|
| **API Web** | NestJS (este proyecto) | Auth, Catálogo, Carrito, Cotizaciones, Solicitudes, Usuarios, Chats |
| **IA/RAG** | Python FastAPI (`../rag-agent`) | Chat con function calling, Embeddings, Vector Search (ChromaDB), Ollama |
| **Base de Datos** | PostgreSQL (compartida) | Ambos backends conectados a la misma BD |
| **Frontend** | Svelte (`../rag-frontend`) | Consume API de NestJS (mismos endpoints que FastAPI) |

## Endpoints Principales

### Auth
- `POST /api/auth/register` - Registro de usuario
- `POST /api/auth/login` - Inicio de sesión
- `GET /api/auth/me` - Usuario actual
- `GET /api/auth/google/login` - Login con Google
- `GET /api/auth/google/callback` - Callback OAuth Google

### Catálogo
- `GET /api/catalog` - Listar categorías con resumen
- `GET /api/maquinaria` - Listar máquinas (filtros: categoriaId, estado, search)
- `GET /api/maquinaria/:id` - Máquina por ID
- `GET /api/maquinaria/nombre/:nombre` - Máquina por nombre exacto
- `GET /api/maquinaria/buscar/:termino` - Buscar maquinaria
- `GET /api/proyectos` - Listar proyectos
- `GET /api/proyectos/:nombre` - Proyecto por nombre
- `GET /api/disponibilidad/:maquinaId` - Verificar disponibilidad (query: fecha_inicio, fecha_fin)

### Carrito (requiere auth)
- `GET /api/carrito` - Obtener carrito
- `POST /api/carrito` - Agregar item
- `DELETE /api/carrito/:itemId` - Eliminar item
- `DELETE /api/carrito/maquina/:maquinaNombre` - Eliminar items de una máquina
- `DELETE /api/carrito` - Vaciar carrito

### Cotizaciones
- `POST /api/cotizacion/calcular` - Calcular cotización (sin guardar)
- `POST /api/cotizacion` - Generar cotización formal (requiere auth)
- `GET /api/cotizaciones` - Mis cotizaciones (requiere auth)
- `GET /api/cotizaciones/:folio` - Cotización por folio (requiere auth)

### Solicitudes (requiere auth)
- `POST /api/solicitudes` - Registrar solicitud de renta
- `GET /api/solicitudes` - Mis solicitudes
- `GET /api/solicitudes/:folio` - Solicitud por folio
- `POST /api/solicitudes/:folio/cancelar` - Cancelar solicitud
- `POST /api/carrito/checkout` - Convertir carrito en solicitud

### Chats (requiere auth)
- `GET /api/chats` - Listar chats
- `POST /api/chats` - Crear chat
- `PUT /api/chats/:chatId` - Actualizar chat
- `DELETE /api/chats/:chatId` - Eliminar chat
- `GET /api/chats/:chatId/messages` - Mensajes de un chat

### Proxy IA (hacia Python FastAPI)
- `POST /v1/chat/completions` - Chat completions (proxy)
- `POST /v1/chat/completions/stream` - Chat streaming SSE (proxy)
- `GET /v1/tools` - Esquemas de herramientas (proxy)
- `POST /v1/rag/query` - Consulta RAG directa (proxy)
- `GET /v1/rag/stats` - Estadísticas RAG (proxy)

### Health
- `GET /api/health` - Health check

## Variables de Entorno

```env
# NestJS Backend
PORT=3000
NODE_ENV=development
FRONTEND_URL=https://rentek-frontend.onrender.com

# Database (shared with Python backend)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=rentek
DB_SYNCHRONIZE=false
DB_LOGGING=false

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-in-production-min-32-chars
JWT_EXPIRES_IN=7d
JWT_REFRESH_EXPIRES_IN=30d

# Google OAuth (optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/google/callback

# Servicio rag-agent
RAG_AGENT_URL=http://localhost:8000
RAG_AGENT_TIMEOUT=60000

# CORS
ALLOWED_ORIGINS=https://rentek-frontend.onrender.com,http://localhost:5173
```

## Desarrollo Local

```bash
# Instalar dependencias
cd /home/damaya/Descargas/Rentek/rag-api
pnpm install

# Copiar .env.example a .env y configurar
cp .env.example .env

# Ejecutar en modo desarrollo
pnpm start:dev

# Build para producción
pnpm build
pnpm start:prod
```

## Docker

```bash
# Desde la raíz del proyecto (/home/damaya/Descargas/Rentek)
docker compose up -d

# Ver logs
docker compose logs -f rag-api
```

## Estructura del Proyecto

```
src/
├── app.module.ts           # Módulo principal
├── main.ts                 # Entry point con Swagger y CORS
├── config/
│   └── configuration.ts    # Configuración centralizada
├── database/
│   └── database.module.ts  # TypeORM configuration
├── health/
│   ├── health.controller.ts
│   └── health.module.ts
└── modules/
    ├── auth/               # Autenticación (JWT, Local, Google OAuth)
    ├── users/              # Gestión de usuarios
    ├── catalog/            # Catálogo de maquinaria
    ├── cart/               # Carrito de compras
    ├── quotes/             # Cotizaciones
    ├── requests/           # Solicitudes de renta
    ├── chats/              # Historial de chats
    └── proxy/              # Proxy al servicio rag-agent (IA/RAG)
```

## Documentación API

Swagger UI disponible en: `http://localhost:3000/api/docs`

## Notas Importantes

1. **Base de datos compartida**: Ambos backends (rag-api y rag-agent) usan la misma PostgreSQL. Los esquemas SQL están en `../rag-agent/db/init/`.

2. **Proxy al servicio rag-agent**: Los endpoints de chat/IA (`/v1/*`) hacen proxy al servicio rag-agent en `RAG_AGENT_URL`. Asegúrate de que el servicio rag-agent esté corriendo.

3. **Frontend compatible**: El frontend Svelte existente (`../rag-frontend`) funciona sin cambios, ya que los endpoints son compatibles.

4. **Migración de datos**: Si migras a la arquitectura separada, ejecuta los scripts de seed de Python para poblar la BD.

## Scripts Útiles

```bash
# Verificar conexión a BD
pnpm typeorm migration:run

# Generar migración
pnpm typeorm migration:generate -- src/migrations/NombreMigracion

# Ejecutar tests
pnpm test
pnpm test:e2e
```