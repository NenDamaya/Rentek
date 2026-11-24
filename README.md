# Rentek — Renta de maquinaria pesada

Tres proyectos independientes que se comunican por HTTP:

| Proyecto | Carpeta | Rol | Puerto local |
|---|---|---|---|
| Frontend | `rag-frontend/` | Svelte + Vite. UI del chat y catálogo. | 5173 |
| API | `rag-api/` | NestJS. Auth, usuarios, catálogo, carrito, cotizaciones, solicitudes, chats. | 3000 |
| RAG / chat | `rag-agent/` | FastAPI. Recuperación, herramientas, orquestación del LLM y streaming. | 8000 |
| LLM | contenedor `ollama` | tag `rag-agent` (base `qwen2.5:7b`) + `nomic-embed-text` sobre GPU. | 11434/11435 |

## Estado de la separación

- [x] Cada proyecto tiene su propio código, Dockerfile y variables de entorno.
- [x] El frontend ya no envía los 20 esquemas de herramientas: el servicio RAG elige el subconjunto según la intención.
- [ ] El frontend sigue apuntando directamente al servicio RAG (`VITE_API_URL`).
- [ ] Auth/chats/catálogo están duplicados entre NestJS y FastAPI.
- [ ] Falta que NestJS sea la única entrada pública y FastAPI quede como servicio interno de IA.

### Arquitectura objetivo

```
Svelte (Render)
      │  HTTPS
      ▼
NestJS API :3000  ──────────────►  PostgreSQL
      │  HTTP interno
      ▼
FastAPI RAG :8000  ──────────────►  Ollama :11434
```

Mientras se completa la migración, el orden recomendado es:

1. Mantener el frontend apuntando a FastAPI (estado actual, funciona).
2. Mover por módulos a NestJS y verificar cada uno contra la misma base de datos.
3. Cuando NestJS cubra todos los endpoints del frontend, cambiar `VITE_API_URL` a NestJS.
4. Dejar en FastAPI solo `/v1/chat/*`, `/v1/tools` y `/api/rag/*`.

## Arranque con Docker (raíz)

```bash
docker compose up -d --build
```

Servicios: `postgres`, `ollama`, `ollama-init` (crea el modelo `rag-agent`),
`rag-agent` (RAG/chat) y `rag-api` (API).
El frontend se compila aparte (Render o `pnpm build` en `rag-frontend/`).

## Presupuesto de contexto

El modelo corre en una RTX 4050 Laptop de 6 GB. La configuración por defecto
prioriza estabilidad sobre ventanas de contexto grandes:

| Variable | Valor | Motivo |
|---|---|---|
| `NUM_CTX` | 8192 | Cabe junto al modelo Q4 en 6 GB con KV cache q8_0. |
| `NUM_PREDICT` | 768 | Respuestas de asesor; no reservar medio contexto. |
| `COMPACT_THRESHOLD_TOKENS` | 3000 | Compacta antes de que Ollama trunque el prompt. |
| `TOOL_RESULT_MAX_CHARS` | 1800 | Evita que un resultado de herramienta desplace el historial. |
| `MAX_TOOL_ROUNDS` | 4 | Limita cadenas de tool calling. |

Si se necesita más contexto, subir `NUM_CTX` de forma gradual y vigilar la VRAM
con `nvidia-smi`; nunca subirlo a 32k de golpe.

## Variables de entorno

Cada proyecto tiene su plantilla:

- `rag-frontend/.env` → `VITE_API_URL`
- `rag-api/.env` → ver `.env.example`
- `rag-agent/.env` → ver `.env.example`

No compartas secretos entre proyectos: el `JWT_SECRET` debe ser el mismo solo
mientras ambos backends validen los mismos tokens.

## Documentación

- `docs/seguridad-rentek.md` — análisis y controles de seguridad.
- `docs/DATABASE_DIAGRAM.md` — esquema de la base de datos.
- `docs/TESTING.md` — pruebas y comandos.
- `docs/auditorias/` — reportes de auditoría del frontend.
- `docs/historial/` — resumen histórico del proyecto.
- `docs/Actividad_*.docx` — entregables.

## Ollama en Fedora (host)

```bash
# 1. Repos RPM Fusion y driver NVIDIA (si no lo tienes)
sudo dnf install -y \
  https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
  https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
sudo dnf install -y akmod-nvidia xorg-x11-drv-nvidia-cuda
sudo reboot

# 2. Verificar GPU
nvidia-smi

# 3. Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 4. Habilitar el servicio
sudo systemctl enable --now ollama
sudo systemctl status ollama --no-pager

# 5. Descargar la base y crear el tag del chat
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
cd /home/damaya/Documentos/Rentek/rag-agent
ollama create rag-agent -f Modelfile
ollama list
```

Con Docker no necesitas los pasos 3–5: el servicio `ollama-init` crea
`rag-agent` automáticamente al hacer `docker compose up`.

### pnpm

El frontend y la API usan **pnpm**:

```bash
corepack enable
corepack prepare pnpm@10.34.9 --activate
pnpm --version

cd rag-api && pnpm install
cd ../rag-frontend && pnpm install
```
