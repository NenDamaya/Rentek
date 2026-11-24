# Rentek - Asistente de Renta de Maquinaria Pesada

## Estado actual

| Componente | Estado | URL |
|------------|--------|-----|
| Frontend (Svelte) | En Render | https://rentek-frontend.onrender.com |
| Backend (FastAPI) | En laptop via ngrok | https://washroom-raffle-unharmed.ngrok-free.dev |
| Ollama (GPU) | En laptop | localhost:11435 (RTX 4050) |
| PostgreSQL | En laptop | localhost:5432 |

## Arquitectura

```
Render (Frontend Static Site)
    │
    ▼ HTTPS
ngrok (tunnel)
    │
    ▼
Laptop (Backend + Ollama + PostgreSQL)
```

## Estructura de carpetas

```
/home/damaya/Descargas/Rentek/
├── rag-frontend/              ← GitHub: NenDamaya/Rentek_Frontend
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api.js         ← API client (VITE_API_URL)
│   │   │   ├── Chat.svelte    ← Componente principal del chat
│   │   │   ├── Message.svelte ← Burbujas de mensaje
│   │   │   ├── ToolCall.svelte
│   │   │   └── VoiceButton.svelte
│   │   ├── App.svelte
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
│
└── rag-agent/               ← En laptop, expuesto via ngrok
    ├── src/                   ← Paquete Python
    │   ├── api.py             ← FastAPI app (uvicorn)
    │   ├── config.py          ← Configuración (env vars)
    │   ├── catalogo.py        ← Parser del catálogo Markdown
    │   ├── database.py        ← Conexión PostgreSQL
    │   ├── ollama_client.py   ← Cliente Ollama (chat + embeddings)
    │   ├── operaciones.py     ← Lógica de negocio
    │   ├── pricing.py         ← Cálculo de precios
    │   ├── rag.py             ← Sistema RAG
    │   ├── reranker.py        ← Re-ranking de resultados
    │   ├── security.py        ← Rate limiting + anti-injection
    │   ├── sessions.py        ← Gestión de sesiones
    │   ├── text_chunker.py    ← Chunking de documentos
    │   ├── tools_schemas.py   ← Schemas de function calling
    │   └── vector_store.py    ← ChromaDB
    ├── db/
    │   ├── init/              ← SQL schemas (4 archivos)
    │   ├── seed.py            ← Seed del catálogo
    │   └── seed_business.py   ← Seed de datos de negocio
    ├── data/documentos/
    │   └── Maquinarias.md     ← Catálogo fuente
    ├── scripts/main.py        ← CLI tool
    ├── docs/                  ← Documentación
    ├── docker-compose.yml
    ├── Dockerfile
    └── requirements.txt
```

## Cómo iniciar

### Backend (laptop)
```bash
cd /home/damaya/Descargas/Rentek/rag-agent
docker compose up -d

# Arrancar ngrok (dominio fijo)
ngrok http --domain=washroom-raffle-unharmed.ngrok-free.dev 8000
```

### Frontend (desarrollo local)
```bash
cd /home/damaya/Descargas/Rentek/rag-frontend
pnpm install
pnpm dev
```

### Frontend (Render)
- Repo: `NenDamaya/Rentek_Frontend`
- Build: `pnpm install && pnpm build`
- Publish: `dist`
- Env var: `VITE_API_URL=https://washroom-raffle-unharmed.ngrok-free.dev`

## Variables de entorno importantes

| Variable | Ubicación | Valor |
|----------|-----------|-------|
| `VITE_API_URL` | Render / frontend | `https://washroom-raffle-unharmed.ngrok-free.dev` |
| `OLLAMA_BASE_URL` | docker-compose | `http://ollama:11434` |
| `OLLAMA_MODEL` | docker-compose | `qwen2.5:7b` |
| `EMBEDDING_MODEL` | docker-compose | `nomic-embed-text` |

## Bugs corregidos en esta sesión

1. **Mensajes desaparecían** - `Chat.svelte` usaba `slice(0,-1)` que eliminaba el mensaje del usuario
2. **Tool calls mostraban "undefined"** - Backend no enviaba `arguments` en el SSE
3. **Crash por `None`** - `execute_tool` retornaba `None` y el backend hacía `"error" not in None`
4. **ngrok interstitial** - Agregado `User-Agent: rentek-app/1.0` a todos los fetch
5. **GPU no detectada** - docker-compose sin config de NVIDIA
6. **Modelo explicaba antes de tool call** - System prompt actualizado para ejecutar sin texto previo

## SSH Configuration

```
~/.ssh/config
├── Host github.com          → id_ed25519_github
└── Host github-nendamaya    → id_ed25519_gh_NenDamaya
```

Remote del frontend: `git@github-nendamaya:NenDamaya/Rentek_Frontend.git`

## Cuentas y servicios

| Servicio | Cuenta |
|----------|--------|
| GitHub | NenDamaya |
| ngrok | washroom-raffle-unharmed.ngrok-free.dev |
| Render | (tu cuenta) |
