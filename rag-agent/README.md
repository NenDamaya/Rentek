# RAG Agent - Asesor de Maquinaria Pesada (chat)

API FastAPI para el agente de chat y RAG de renta de maquinaria pesada. Corre en la laptop y se expone via ngrok.

El LLM se sirve con Ollama con dos tags:

- `rag-agent:8b` — chat principal (respeta `think:false`).
- `rag-agent:4b` — generación JSON estructurada (paquetes).

```bash
ollama pull qwen3:8b
ollama pull qwen3:4b
ollama pull bge-m3
ollama create rag-agent:8b -f Modelfile
ollama create rag-agent:4b -f Modelfile.4b
```

## Stack

- Python 3.12
- FastAPI + Uvicorn
- PostgreSQL 16
- Ollama (GPU) - qwen3:8b (chat) / qwen3:4b (JSON) + bge-m3

## Correr con Docker

```bash
docker compose -f docker-compose.backend.yml up -d
```

## Exponer con ngrok

```bash
ngrok http 8000
```

## Endpoints

- `GET /` - Status de la API
- `POST /v1/chat/completions` - Chat con function calling
- `POST /v1/chat/completions/stream` - Chat con streaming SSE
- `GET /v1/tools` - Schema de herramientas disponibles
- `GET /api/maquinaria` - Catalogo de maquinaria
- `GET /api/maquinaria/buscar/{termino}` - Buscar maquinaria
- `GET /api/proyectos` - Proyectos disponibles
- `GET /api/stats` - Estadisticas del sistema
- `POST /api/db/seed` - Poblar base de datos

## Variables de entorno

| Variable | Default |
|----------|---------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` |
| `OLLAMA_MODEL` | `rag-agent:8b` |
| `OLLAMA_THINK` | `false` |
| `EMBEDDING_MODEL` | `bge-m3` |
| `DB_HOST` | `postgres` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `maquinaria_rag` |
| `DB_USER` | `rag_user` |
| `DB_PASSWORD` | `rag_pass_2026` |
