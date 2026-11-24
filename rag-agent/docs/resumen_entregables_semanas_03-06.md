# Resumen de Entregables — Proyecto de IA Local (Semanas 3 a 6)

> Equipos de 3 personas. Cada semana requiere **documento técnico** + **video público en redes sociales**, con participación de todos los integrantes.

---

## Semana 3: RAG (Conocimiento Estático) + Function Calling (Conocimiento Dinámico)

### Fase 1 — Base de Datos Vectorial (RAG)
- Ingesta de documentos: chunking + embeddings.
- Almacenamiento e indexación en ChromaDB, Qdrant, pgvector o LanceDB (métrica de distancia, ej. coseno).
- Lógica de recuperación (retrieval) semántico para inyectar contexto al LLM.
- Meta de calidad: recall 90–95%, latencia p95 < 100ms, respuestas 100% fieles al contexto (sin alucinar).

**Entregable Fase 1:** Video demostrativo público explicando arquitectura, flujo de ingesta y demo en vivo.

### Fase 2 — Function Calling
- Modelos locales compatibles con tools (Llama 3.1 8B, Qwen 2.5 Coder, Mistral-Nemo).
- Funciones backend con **type hints + docstrings** obligatorios.
- Envío del esquema de funciones en el parámetro `tools`.
- Interceptar `tool_calls`, ejecutar función real, y devolver resultado con `role: 'tool'`.
- Evitar que errores de función se guarden permanentemente en memoria (estado fallido en bucle).
- Entre **7 y 15 funciones locales** disponibles para el LLM.

**Entregables Fase 2:**
1. Documento técnico detallando la implementación.
2. Lista de funciones (7–15).
3. Video mostrando el flujo completo: pregunta → JSON generado → ejecución interceptada → respuesta final.

### Roles del equipo
1. Arquitecto de Datos/Backend (BD vectorial + funciones API).
2. Ingeniero LLM (prompts, modelos, orquestación de `tools`).
3. Arquitecto de QA (métricas, manejo de errores, auditoría).

---

## Semana 4: Persistencia de Memoria (Stateful)

Transición de interacciones de un solo turno a conversaciones multi-turno persistentes.

### Puntos clave a implementar
- **A. `conversation_id`**: identificador único (UUID/hash) por conversación; el backend crea o recupera historial según se provea o no.
- **B. Almacenamiento del historial**: idealmente BD embebida/relacional (SQLite, PostgreSQL) en vez de solo memoria RAM (volátil).
- **C. Flujo de prompting**: reconstruir contexto completo (system, user, assistant, tool) en cada request.
- **D. Gestión de ventana de contexto**: recorte (sliding window) o resumen (summarization) para evitar desbordes de tokens/VRAM.
- **E. Resiliencia ante errores de function calling**: errores no deben "envenenar" la memoria (State Poisoning) ni causar bucles infinitos.
- **F. Bitácora de decisiones**: anexo con fuentes/benchmarks que justifiquen modelo, tamaño de ventana de contexto y elección de BD.

### Entregables
1. **Documento técnico (Markdown)**: arquitectura de persistencia, estructura de BD/sesiones, flujo de control, y la Bitácora de Decisiones (punto F).
2. **Video explicativo**: arquitectura de persistencia, demo en vivo manteniendo contexto, y cómo se evitó que errores corrompieran la memoria. Publicado en redes.

---

## Semana 5: UX/Voz, Seguridad y Observabilidad

### Fase A — Interfaz de Usuario y Voz
- Cliente web/móvil (React, Vue, Angular o vanilla) conectado al backend de la semana 4, responsivo y moderno.
- **Streaming** de respuestas vía SSE o WebSockets (efecto "máquina de escribir").
- **Indicadores de carga dinámicos** diferenciando: pensando (LLM), buscando (BD), ejecutando acción (function calling).
- **Entrada de voz (STT)** obligatoria:
  - Opción base: Whisper local (whisper-node, faster-whisper, whisper.cpp).
  - Si no es viable por hardware: justificar con benchmarks (consumo CPU/GPU/VRAM) y usar alternativa (Web Speech API, Sherpa-ONNX, Whisper Tiny Q4_0).

### Fase B — Seguridad y Observabilidad
- **Guardrails**: middleware que detecte intentos de prompt injection (fuga de instrucciones, jailbreaks) sin invocar al LLM si se bloquea.
- **Tabla de observabilidad** en BD con campos mínimos: `id`, `session_id`, `timestamp`, `user_prompt`, `system_response`, `ttft_ms`, `total_latency_ms`, `tokens_per_second`, `was_blocked`, `tools_executed` (JSON).

### Entregables
1. **Documento técnico en PDF** (`entregable.semana.05.pdf`):
   - Portada, arquitectura del sistema (diagrama/Mermaid), detalle de implementación con código, bitácora de observabilidad (capturas de BD), reflexiones individuales (3 integrantes), justificación de alternativa de voz (si aplica).
2. **Video demostrativo público**: portada formal, explicación de arquitectura frontend/guardrails, demo en vivo de streaming + indicador de carga + bloqueo de inyección de prompt + interacción por voz, y logs de observabilidad en tiempo real. Todos participan.

---

## Semana 6: Docker y Exposición Pública

### Fase A — Dockerización
- Dockerfile para frontend y backend (idealmente multi-stage build).
- `docker-compose.yml` con al menos 3 servicios: `frontend`, `backend`, `database` (o volumen persistente si es SQLite).
- Conexión a Ollama en el host vía `host.docker.internal` (GPU puede correr nativa en el host).
- Volúmenes persistentes para que la BD de observabilidad no se reinicie en blanco.
- **Excepciones**: si usan Supabase, no se exige contenedor de BD; si usan Vercel/Netlify/etc., no se exige contenedor de frontend (pero el backend sí es obligatorio en Docker Compose).

### Fase B — Exposición pública
- Túnel inverso: **Cloudflare Quick Tunnels**, **Ngrok Free Tier**, o **VPS** (DigitalOcean, AWS, GCP, Azure).
- Si el frontend está en Vercel/similar, el túnel debe apuntar al backend local; si el frontend es local, el túnel apunta al frontend.
- Configurar **CORS** correctamente entre dominios distintos (frontend en la nube ↔ backend expuesto vía túnel).

### Entregables
1. **Documento técnico en PDF** (`entregable.semana.06.pdf`):
   - Portada, diagrama de arquitectura de red/contenedores (Mermaid), copia comentada de `docker-compose.yml` y Dockerfiles, evidencias del túnel activo y peticiones externas (ej. desde 4G/5G), **análisis comparativo de latencia** (local vs. público: TTFT y latencia total), reflexiones individuales.
2. **Video demostrativo público**: portada formal, explicación de Docker Compose, demo en vivo desde un dispositivo móvil externo (fuera de la red local) usando la URL pública del túnel, logs de los contenedores en tiempo real. Todos participan.

---

## Progresión general del proyecto

| Semana | Enfoque | Entregable documento | Entregable video |
|---|---|---|---|
| 3 | RAG + Function Calling | Doc. de function calling | Video RAG + Video function calling |
| 4 | Memoria persistente (stateful) | Doc. en Markdown + bitácora de decisiones | Video de arquitectura de persistencia |
| 5 | UX/Voz + Seguridad + Observabilidad | Doc. en PDF (`entregable.semana.05.pdf`) | Video con demo de streaming, voz y seguridad |
| 6 | Docker + Exposición pública | Doc. en PDF (`entregable.semana.06.pdf`) | Video con demo de acceso público vía túnel |
