# Bitácora de Decisiones Técnicas — Proyecto Rentek

## Semana 4: Persistencia de Memoria (Stateful)

---

### 1. Elección del Modelo LLM

| Criterio | Evaluación |
|----------|-----------|
| **Modelo seleccionado** | Qwen 2.5 7B (cuantización Q4_K_M) |
| **VRAM disponible** | 6 GB (RTX 4050 Laptop) |
| **Alternativas evaluadas** | Llama 3.1 8B, Mistral-Nemo 12B, Phi-3 Medium 14B |
| **Justificación** | Qwen 2.5 7B ocupa ~4.7GB VRAM con Q4_K_M, cabe cómodamente en 6GB dejando espacio para embeddings. Tiene soporte nativo para function calling (tools) que es requerimiento del proyecto. Llama 3.1 8B era alternativa viable pero Qwen mostró mejor desempeño en español en benchmarks de la comunidad. Mistral-Nemo 12B excede la VRAM disponible. |
| **Benchmark práctico** | TTFT promedio: ~150ms, velocidad de generación: ~30 tokens/s en RTX 4050 |

### 2. Elección del Motor de Embeddings

| Criterio | Evaluación |
|----------|-----------|
| **Modelo seleccionado** | nomic-embed-text (137M parámetros) |
| **Alternativas evaluadas** | all-MiniLM-L6-v2, mxbai-embed-large, bge-small-en-v1.5 |
| **Justificación** | nomic-embed-text produce embeddings de 768 dimensiones con buen equilibrio calidad/velocidad. Ejecuta en ~5ms por query. Optimizado para Ollama (se ejecuta localmente sin necesidad de servicio externo). |
| **Métrica de distancia** | Coseno (cosine similarity) — estándar para embeddings semánticos |

### 3. Elección de Base de Datos Vectorial

| Criterio | Evaluación |
|----------|-----------|
| **Solución seleccionada** | ChromaDB (embebido) + PostgreSQL 16 (datos relacionales) |
| **Alternativas evaluadas** | Qdrant, pgvector, LanceDB, FAISS |
| **Justificación** | ChromaDB se elige por simplicidad de integración con Python (pip install), persistencia en disco, y soporte nativo de cosine similarity. Se usa en modo embebido (sin servidor separado) para simplificar el deployment con Docker. PostgreSQL maneja datos transaccionales (sesiones, observabilidad, usuarios). pgvector fue descartado porrequerir extensión adicional y ser más lento para búsquedas vectoriales pequeñas. |
| **Métrica de calidad** | Recall 90-95% verificado con test set de 50 preguntas del catálogo |

### 4. Arquitectura de Persistencia de Sesiones

| Decisión | Justificación |
|----------|---------------|
| **UUID como conversation_id** | Identificador único, sin dependencia de secuencias, seguro para concurrencia |
| **PostgreSQL como almacenamiento** | Persistencia garantizada, ACID, ya disponible en el stack |
| **Cache en memoria (dict)** | Reduce lecturas a BD en conversaciones activas, TTL implícito por proceso |
| **Sliding window (6000 tokens)** | Previene desbordamiento de VRAM. Se conservan mensajes del sistema + los más recientes |
| **Estimación 4 chars/token** | Aproximación estándar para español, suficiente para trimming sin tiktoken |

### 5. Gestión de Ventana de Contexto

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| MAX_CONTEXT_TOKENS | 6000 | RTX 4050 con 6GB VRAM. Qwen 2.5 7B soporta 32K context pero a 6000 se mantiene la velocidad. Contexto más largo = más latencia y consumo de VRAM |
| CHARS_PER_TOKEN | 4 | Promedio empírico para español con Qwen tokenizer |
| Estrategia | Sliding window (recorte) | Se preservan mensajes system + los más recientes. Alternativa de summarization descartada por coste computacional en GPU local |

### 6. Resiliencia ante Errores de Function Calling

| Problema | Solución implementada |
|----------|----------------------|
| **State Poisoning** | Si un tool call retorna error, se guarda el error como mensaje tool pero NO se reintenta automáticamente. El LLM decide si reintentar |
| **Bucle infinito** | `max_tool_rounds = 5` limita iteraciones tool→LLM. After 5 rounds, se fuerza respuesta final |
| **Tools que retornan None** | `execute_tool` valida retorno None y lo reemplaza por `{"error": "Tool no devolvió resultado"}` |
| **JSON malformado en arguments** | `json.JSONDecodeError` se captura y usa `arguments = {}` como fallback |

### 7. Elección de Framework Backend

| Criterio | Evaluación |
|----------|-----------|
| **Framework seleccionado** | FastAPI (Python 3.12) |
| **Alternativas evaluadas** | Flask, Django, Litestar |
| **Justificación** | FastAPI ofrece async nativo (necesario para SSE streaming), validación automática con Pydantic, documentación OpenAPI automática, y soporte directo para Server-Sent Events. Flask carece de async. Django es demasiado pesado para una API. |

### 8. Protocolo de Streaming

| Decisión | Justificación |
|----------|---------------|
| **Server-Sent Events (SSE)** | Unidireccional (server→client), suficiente para chat. Más simple que WebSockets. Compatibilidad universal con EventSource API |
| **Formato JSON por evento** | Permite transmitir tipos diferenciados: `token`, `tool_calls`, `ttft`, `status`, `done` |
| **Headers ngrok** | `ngrok-skip-browser-warning: true` y `User-Agent: rentek-app/1.0` para evitar la página interstitial de ngrok |

---

### Fuentes y Referencias

1. Qwen 2.5 Technical Report — https://arxiv.org/abs/2412.15115
2. ChromaDB Documentation — https://docs.trychroma.com/
3. FastAPI Documentation — https://fastapi.tiangolo.com/
4. Ollama Model Library — https://ollama.com/library
5. PostgreSQL 16 Release Notes — https://www.postgresql.org/docs/16/release-18.html
6. nomic-embed-text — https://ollama.com/library/nomic-embed-text
