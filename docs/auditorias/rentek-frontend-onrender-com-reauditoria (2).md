# Re-Auditoría de Seguridad — Rentek (Asistente de Maquinaria Pesada)

**Sitio:** rentek-frontend.onrender.com  
**Backend:** washroom-raffle-unharmed.ngrok-free.dev  
**Fecha:** 28 de julio de 2026  
**Tipo:** Re-auditoría (anterior: 2/100 🔴)

---

## Calificación: 45/100 🟠

### Justificación

El equipo realizó mejoras SIGNIFICATIVAS respecto a la auditoría anterior (2/100). Se corrigieron 4 vulnerabilidades críticas, se implementó autenticación correcta en endpoints clave, y se agregó rate limiting. Sin embargo, persisten 3 vulnerabilidades de alto impacto y 4 de impacto medio.

| Eje | Peso | Puntaje | Justificación |
|---|---|---|---|
| **Autenticación y control de acceso** | 35% | 65/100 | Auth funcional con tokens, rate limiting activo, sin IDOR. Pero `/api/stats` y `/api/query` sin auth. User enumeration posible. |
| **Seguridad del AI Agent** | 30% | 35/100 | Guardrails mejorados contra prompt injection. Pero AI puede ser manipulado vía tool calling (`registrar_solicitud`). RAG query endpoint público. |
| **Infraestructura y hardening** | 35% | 35/100 | Cloudflare + HSTS ✓. Pero backend via ngrok, `/api/transcribe` retorna 500, `/api/stats` expone configuración interna. |

**Cálculo:** `(65 × 0.35) + (35 × 0.30) + (35 × 0.35) = 22.75 + 10.5 + 12.25 = 45.5 ≈ 45`

**Mejora desde la última auditoría: 2/100 → 45/100 (+43 puntos)**

---

## Comparativa: Antes vs Ahora

| Vulnerabilidad | Antes (2/100) | Ahora (45/100) | Estado |
|---|---|---|---|
| CORS con origen arbitrario | 🔴 CRÍTICO | Sin headers CORS abiertos | ✅ CORREGIDO |
| `/api/ingest` sin auth | 🔴 CRÍTICO | `Autenticación requerida` | ✅ CORREGIDO |
| `/api/db/seed` sin auth | 🔴 CRÍTICO | `Autenticación requerida` | ✅ CORREGIDO |
| Price manipulation | 🟠 ALTO | Precios calculados del servidor | ✅ CORREGIDO |
| Rate limiting | ❌ Ausente | 5 intentos → 429 Too Many | ✅ CORREGIDO |
| Token tampering | 🔴 CRÍTICO | Token validado correctamente | ✅ CORREGIDO |
| Auth en endpoints API | ❌ Múltiples abiertos | Ahora protegidos con Bearer | ✅ CORREGIDO |
| AI prompt injection | 🔴 CRÍTICO | Guardrails mejorados (parcial) | ⚠️ PARCIAL |
| `/api/query` sin auth | 🟠 ALTO | Sigue abierto | ❌ PERSISTE |
| `/api/stats` sin auth | 🟡 MEDIO | Sigue abierto | ❌ PERSISTE |
| Backend via ngrok | 🟡 MEDIO | Sigue en ngrok | ❌ PERSISTE |
| `/api/transcribe` bug | 🟡 MEDIO | Retorna 500 ISE | ❌ PERSISTE |

---

## Puntos Descubiertos

### 🟠 Altos (3)

| ID | Hallazgo | Impacto |
|---|---|---|
| **HIGH-01** | **`/api/query` sin autenticación — RAG knowledge base pública.** Cualquier persona puede consultar la base de conocimiento RAG sin token. Retorna `answer` y `sources` con fragmentos completos del knowledge base. Se confirmó que responde con especificaciones técnicas, precios, y descripciones detalladas de maquinaria. | Exposición de la base de conocimiento propietaria. Vector de RAG poisoning si se combina con ingest. |
| **HIGH-02** | **`/api/stats` sin autenticación — fuga de configuración interna.** Retorna `total_documents`, `chunk_size`, `chunk_overlap`, `similarity_metric`, `top_k`, `avg_latency_ms`, `p95_latency_ms`. Sin token requerido. | Información de configuración del sistema RAG útil para atacantes. |
| **HIGH-03** | **AI tool injection vía prompt — creación fraudulenta de registros.** El AI ejecuta la herramienta `registrar_solicitud` cuando se le engaña con contexto falso. Se creó una solicitud con datos inventados ("Juan Admin", "admin@rentek.com") que quedó almacenada en el sistema con folio `SOL-2026-1ED131`. | Posibilidad de crear registros falsos, suplantar clientes, y contaminar el sistema de cotizaciones. |

### 🟡 Medios (4)

| ID | Hallazgo | Impacto |
|---|---|---|
| **MED-01** | **`/api/transcribe` retorna 500 Internal Server Error.** Tanto con archivos de audio reales como con archivos falsos. El error no revela stack trace pero la respuesta es texto plano sin JSON. | Endpoint funcionalmente roto. No se puede determinar si hay exposición de datos. |
| **MED-02** | **User enumeration vía registro.** Al intentar registrar un email existente devuelve `"El correo ya está registrado"` vs un email nuevo que devuelve éxito con token. | Permite a un atacante verificar qué correos están registrados en el sistema. |
| **MED-03** | **Backend expuesto via ngrok con IP real visible.** `ngrok-agent-ips: 187.251.136.169` expuesto en headers de respuesta. Backend sin WAF ni protección perimetral. | Fingerprinting de infraestructura, posible ataque directo a la IP del servidor. |
| **MED-04** | **Chat AI expone latencia y tiempos de procesamiento.** El endpoint `/v1/chat/completions/stream` revela `ttft` (time to first token = 263ms) y latencia de búsqueda. | Información de rendimiento interna que ayuda a un atacante a entender la arquitectura. |

### 🟢 Bajos (3)

| ID | Hallazgo | Impacto |
|---|---|---|
| **LOW-01** | **Modelo AI es qwen2.5:7b vía Ollama** (mismo que antes). El endpoint `/v1/tools` revela las 18 herramientas disponibles. | Sin impacto directo pero útil para reconocimiento. |
| **LOW-02** | **El carrito de compras expone `maquina_json` con datos como `nombre`, `categoria`, `nombre_comun`, `precio_renta`.** | Solo datos que ya son públicos en el catálogo. |
| **LOW-03** | **Sin documentación de API ni OpenAPI expuesta.** No hay `/docs`, `/redoc`, ni `/openapi.json`. | Dificulta el testing legítimo pero no es una vulnerabilidad. |

---

## Áreas de Mejora

### Inmediatas

| # | Acción | Área | Esfuerzo |
|---|---|---|---|
| 1 | Agregar autenticación a `/api/query` | RAG Security | 1 hora |
| 2 | Agregar autenticación a `/api/stats` o restringir a admin | Info Leak | 1 hora |
| 3 | Validar que el AI no ejecute `registrar_solicitud` sin confirmación explícita del usuario | IA Security | 1-2 días |
| 4 | Agregar CAPTCHA o retardo progresivo al registro para evitar user enumeration | Hardening | 1 día |
| 5 | Reparar `/api/transcribe` o removerlo si no se usa | Bug Fix | 1 día |

### Corto Plazo

| # | Acción | Área |
|---|---|---|
| 6 | Migrar backend a IP fija con dominio propio y WAF (Cloudflare) | Infraestructura |
| 7 | Implementar rol de administrador real con endpoints separados y auditados | Auth |
| 8 | Agregar logging de todas las herramientas ejecutadas por el AI con datos de auditoría | IA Security |
| 9 | Implementar rate limiting también en `/v1/chat/completions` | Hardening |
| 10 | Agregar rate limiting en registro (3 intentos por IP por hora) | Hardening |

### Mediano Plazo

| # | Acción |
|---|---|
| 11 | Implementar 2FA para cuentas de administrador |
| 12 | Realizar pruebas de penetración con equipo especializado en LLM security |
| 13 | Implementar Content Security Policy con nonces |
| 14 | Agregar monitoreo de anomalías en herramientas ejecutadas por el AI |

---

## Resumen de Hallazgos

| ID | Hallazgo | Severidad | CVSS |
|---|---|---|---|
| HIGH-01 | `/api/query` sin auth — RAG pública | 🟠 ALTO | 7.5 |
| HIGH-02 | `/api/stats` sin auth — fuga configuración | 🟠 ALTO | 6.5 |
| HIGH-03 | AI tool injection — registros fraudulentos | 🟠 ALTO | 7.0 |
| MED-01 | `/api/transcribe` 500 error | 🟡 MEDIO | 4.0 |
| MED-02 | User enumeration vía registro | 🟡 MEDIO | 3.5 |
| MED-03 | ngrok expone IP real | 🟡 MEDIO | 3.0 |
| MED-04 | Latencia y métricas expuestas | 🟡 MEDIO | 2.5 |
| LOW-01 | Modelo AI y herramientas reveladas | 🟢 BAJO | 1.0 |
| LOW-02 | Carrito expone datos de catálogo | 🟢 BAJO | 1.0 |
| LOW-03 | Sin documentación de API | 🟢 BAJO | 0.5 |

---

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Frontend | Svelte + Vite (SPA) |
| Backend | FastAPI (Python) + Uvicorn |
| Base de datos | PostgreSQL |
| AI Model | Qwen2.5:7b via Ollama |
| RAG | Similarity search (cosine), chunk_size=700, overlap=88 |
| Hosting Frontend | Render.com |
| Backend Proxy | ngrok |
| CDN/WAF | Cloudflare |
| Auth | Bearer tokens con formato `id:email:hash` |

---

## Conclusión

**Progreso notable.** El equipo pasó de un sistema completamente abierto (2/100) a uno con autenticación funcional, rate limiting, y protección contra los vectores de ataque más críticos. 

**Lo que falta:** Endpoints de administración y RAG públicos, protección contra abuso de herramientas del AI, y migración fuera de ngrok. Con esos cambios, Rentek podría alcanzar 70-75/100.

---

*Documento generado como parte de evaluación de seguridad ofensiva — Julio 2026*
*Ambiente controlado — Pruebas de penetración autorizadas*
