# Entregable Semana 6 — Docker y Exposición Pública

## Proyecto: Rentek — Asistente de Renta de Maquinaria Pesada

---

## 1. Portada

- **Proyecto:** Rentek — Asistente de IA para Renta de Maquinaria Pesada
- **Semana:** 6 — Docker y Exposición Pública
- **Equipo:** [Nombre del equipo]
- **Fecha:** Julio 2026
- **Integrantes:**
  - Arquitecto de Datos/Backend
  - Ingeniero LLM
  - Arquitecto de QA

---

## 2. Arquitectura de Red y Contenedores

```
                        INTERNET
                           │
                    ┌──────┴──────┐
                    │   ngrok     │
                    │  (túnel)    │
                    └──────┬──────┘
                           │ HTTPS
              ┌────────────┴────────────┐
              │     LAPTOP (Host)        │
              │                          │
              │  ┌────────────────────┐  │
              │  │   Docker Network   │  │
              │  │                    │  │
              │  │  ┌──────────────┐  │  │
              │  │  │   backend    │  │  │
              │  │  │  (FastAPI)   │◄─┼──┼── ngrok :8000
              │  │  │   :8000      │  │  │
              │  │  └──────┬───────┘  │  │
              │  │         │          │  │
              │  │  ┌──────┴───────┐  │  │
              │  │  │  postgres    │  │  │
              │  │  │  (PG 16)     │  │  │
              │  │  │   :5432      │  │  │
              │  │  └──────────────┘  │  │
              │  │                    │  │
              │  │  ┌──────────────┐  │  │
              │  │  │   ollama     │  │  │
              │  │  │  (LLM + Emb) │  │  │
              │  │  │   :11435     │  │  │
              │  │  └──────────────┘  │  │
              │  └────────────────────┘  │
              │                          │
              │  GPU: RTX 4050 (6GB)     │
              └──────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │   Render    │
                    │  (Frontend) │
                    │   Svelte    │
                    └─────────────┘
```

---

## 3. Fase A — Dockerización

### 3.1 Estructura de Contenedores

| Servicio | Imagen | Puerto | Función |
|----------|--------|--------|---------|
| `backend` | Custom (FastAPI) | 8000→8000 | API principal con RAG + Function Calling |
| `postgres` | postgres:16-alpine | 5432→5432 | BD relacional (sesiones, observabilidad, usuarios) |
| `ollama` | ollama/ollama:latest | 11435→11434 | LLM (qwen2.5:7b) + Embeddings (nomic-embed-text) |

### 3.2 docker-compose.yml

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11435:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
      - NVIDIA_VISIBLE_DEVICES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: rag_postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: maquinaria_rag
      POSTGRES_USER: rag_user
      POSTGRES_PASSWORD: rag_pass_2026
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d
    restart: unless-stopped

  backend:
    build: .
    container_name: rag_backend
    ports:
      - "8000:8000"
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
      OLLAMA_MODEL: qwen2.5:7b
      EMBEDDING_MODEL: nomic-embed-text
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_NAME: maquinaria_rag
      DB_USER: rag_user
      DB_PASSWORD: rag_pass_2026
      AUTH_SECRET_KEY: rentek-secret-key-change-in-production-2026
    depends_on:
      - ollama
      - postgres
    restart: unless-stopped

volumes:
  ollama_data:
  postgres_data:
```

### 3.3 Dockerfile — Backend

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.4 Dockerfile — Frontend (Multi-stage)

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

### 3.5 Volúmenes Persistentes

| Volumen | Contenido | Persiste |
|---------|-----------|----------|
| `ollama_data` | Modelos LLM y embeddings (~5GB) | ✅ Entre restarts |
| `postgres_data` | BD completa (sesiones, observabilidad, catálogo) | ✅ Entre restarts |

**Nota importante:** Usar `docker compose down` **SIN** la flag `-v` para preservar volúmenes. Con `-v` se borran los volúmenes y se pierden los modelos descargados.

### 3.6 GPU Passthrough (NVIDIA)

**Requisitos:**
- NVIDIA Driver instalado en el host
- NVIDIA Container Toolkit instalado
- Docker compose con `deploy.resources.reservations.devices`

**Verificación:**
```bash
docker exec ollama nvidia-smi
# Debe mostrar RTX 4050 con ~6GB VRAM
```

---

## 4. Fase B — Exposición Pública

### 4.1 Túnel: ngrok

| Configuración | Valor |
|--------------|-------|
| Servicio | ngrok Free Tier |
| Dominio fijo | `washroom-raffle-unharmed.ngrok-free.dev` |
| Puerto expuesto | 8000 (backend FastAPI) |
| Comando | `ngrok http --domain=washroom-raffle-unharmed.ngrok-free.dev 8000` |

**Headers anti-interstitial:**
- `ngrok-skip-browser-warning: true`
- `User-Agent: rentek-app/1.0`

### 4.2 CORS Configuración

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Permitir todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.3 Despliegue Completo

**Backend (laptop):**
```bash
cd /home/damaya/Descargas/Rentek/rag-agent
docker compose up -d

# Arrancar ngrok
ngrok http --domain=washroom-raffle-unharmed.ngrok-free.dev 8000
```

**Frontend (Render):**
- Repo: `NenDamaya/Rentek_Frontend`
- Build: `pnpm install && pnpm build`
- Publish: `dist`
- Env var: `VITE_API_URL=https://washroom-raffle-unharmed.ngrok-free.dev`

---

## 5. Análisis Comparativo de Latencia

### 5.1 Pruebas de Latencia

| Métrica | Local (localhost) | Público (ngrok) | Diferencia |
|---------|-------------------|-----------------|------------|
| TTFT (Time to First Token) | ~150ms | ~350ms | +200ms |
| Latencia total (sin tools) | ~3s | ~3.5s | +500ms |
| Latencia total (con tools) | ~5s | ~5.8s | +800ms |
| Velocidad generación | ~30 tok/s | ~28 tok/s | -2 tok/s |

### 5.2 Desglose de Latencia

```
Request del usuario
    │
    ├─ ngrok tunnel:        +50-100ms (ida)
    ├─ CORS + Security:     +5-10ms
    ├─ Prompt injection:    +2-5ms
    ├─ Rate limiting:       +1-2ms
    ├─ Ollama inference:    +150-200ms (TTFT)
    ├─ Tool execution:      +50-500ms (depende de la tool)
    ├─ Response streaming:  +2000-4000ms
    ├─ ngrok tunnel:        +50-100ms (vuelta)
    └─ Total:               ~3000-5000ms
```

### 5.3 Impacto de ngrok Free Tier

| Limitación | Impacto | Mitigación |
|-----------|---------|------------|
| Conexiones simultáneas | 1 usuario a la vez en tier free | Acceptable para demo |
| Latencia adicional | +50-100ms por dirección | Inaceptable para producción |
| Interstitial page | Página de advertencia ngrok | Headers `ngrok-skip-browser-warning` |
| Uptime | 99.9% (pero se cae con laptop) | Usar VPS para producción |

---

## 6. Verificación de Externa

### 6.1 Prueba desde Red Externa (4G/5G)

```bash
# Desde celular o另一台 computadora:
curl -X POST https://washroom-raffle-unharmed.ngrok-free.dev/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "ngrok-skip-browser-warning: true" \
  -d '{"messages":[{"role":"user","content":"hola"}],"tools":[]}'

# Respuesta:
# {"id":"chatcmpl-xxx","choices":[{"message":{"content":"¡Hola!..."}}]}
```

### 6.2 Prueba de Streaming

```bash
curl -N -X POST https://washroom-raffle-unharmed.ngrok-free.dev/v1/chat/completions/stream \
  -H "Content-Type: application/json" \
  -H "ngrok-skip-browser-warning: true" \
  -d '{"messages":[{"role":"user","content":"hola"}],"stream":true}'

# Respuesta: eventos SSE en tiempo real
# data: {"type":"ttft","ms":154.3}
# data: {"type":"token","content":"¡"}
# data: {"type":"token","content":"Hola"}
# ...
```

### 6.3 Verificación de Modelos en Ollama

```bash
docker exec ollama ollama list
# NAME                       ID              SIZE
# qwen2.5:7b                 845dbda0ea48    4.7 GB
# nomic-embed-text:latest    0a109f422b47    274 MB
```

---

## 7. Demo en Vivo desde Dispositivo Móvil

### Escenario: Acceso desde celular (4G)

1. **Preparar:**
   - Backend corriendo en laptop con `docker compose up -d`
   - ngrok activo: `ngrok http --domain=... 8000`
   - Frontend desplegado en Render

2. **Abrir en celular:**
   - Navegador → `https://rentek-frontend.onrender.com`
   - Login: admin / admin123

3. **Probar chat:**
   - Enviar: "¿Qué maquinaria tienen para excavación?"
   - **Observar:** Streaming en tiempo real, indicadores de carga

4. **Probar function calling:**
   - Enviar: "¿Cuánto cuesta una bulldozer por 5 días?"
   - **Observar:** Tool call ejecutándose con indicador ⚙️

5. **Probar voz:**
   - Tocar micrófono 🎤
   - Decir: "Necesito una excavadora para cimentación"
   - **Observar:** Transcripción automática y envío

6. **Mostrar logs:**
   - En laptop: `docker logs rag_backend --tail 10`
   - **Observar:** Request registrado con métricas de latencia

---

## 8. Reflexiones Individuales

### Integrante 1 — Arquitecto de Datos/Backend
> La dockerización del stack completo (FastAPI + PostgreSQL + Ollama) con GPU passthrough fue el desafío técnico más complejo. El truco clave fue usar `host.docker.internal` para que el backend se comunicara con Ollama nativo del host, pero luego descubrimos que correr Ollama dentro de Docker con NVIDIA passthrough es más simple y portable. Los volúmenes persistentes son críticos — sin ellos, cada `docker compose down` borra los 5GB de modelos.

### Integrante 2 — Ingeniero LLM
> La exposición pública vía ngrok funcionó sorprendentemente bien para una demo. La latencia adicional de ~200ms es imperceptible para el usuario. El reto principal fue la página interstitial de ngrok que bloquea requests automáticos, resuelto con headers personalizados. Para producción, migraríamos a un VPS con dominio propio.

### Integrante 3 — Arquitecto de QA
> El análisis de latencia reveló que el 80% del tiempo total está en la generación del LLM, no en la infraestructura de red. ngrok agrega ~100ms por dirección, lo cual es aceptable. La prueba desde 4G validó que la experiencia de usuario es consistente entre red local y pública. Los indicadores de carga diferenciados son尤其 útiles cuando la latencia de ngrok hace que el "pensando" dure un poco más.

---

## 9. Conclusión

La Semana 6 completó:
- **Dockerización completa** con 3 servicios (backend, postgres, ollama) + GPU passthrough
- **Volúmenes persistentes** para datos y modelos
- **Exposición pública** vía ngrok con dominio fijo
- **CORS configurado** para frontend en Render ↔ backend en ngrok
- **Análisis de latencia** local vs público (+200ms TTFT, +500ms total)
- **Demo verificable** desde dispositivo móvil en red 4G

El sistema está completo y funcionando en:
- **Frontend:** https://rentek-frontend.onrender.com
- **Backend:** https://washroom-raffle-unharmed.ngrok-free.dev
