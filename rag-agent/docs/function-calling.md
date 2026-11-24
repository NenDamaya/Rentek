# Documentación del Sistema Function Calling (FASE 3)

## Indice

1. [Arquitectura General](#1-arquitectura-general)
2. [¿Qué es Function Calling?](#2-que-es-function-calling)
3. [Las 14 Herramientas Disponibles](#3-las-14-herramientas-disponibles)
4. [Arquitectura del Backend](#4-arquitectura-del-backend)
5. [Base de Datos de Negocio](#5-base-de-datos-de-negocio)
6. [Lógica de Precios y Descuentos](#6-logica-de-precios-y-descuentos)
7. [Frontend Svelte](#7-frontend-svelte)
8. [Flujo Completo de una Consulta](#8-flujo-completo-de-una-consulta)
9. [Docker y Despliegue](#9-docker-y-despliegue)
10. [Ejemplos de Uso](#10-ejemplos-de-uso)
11. [Justificación de Tecnologías](#11-justificacion-de-tecnologias)
12. [Glosario](#12-glosario)

---

## 1. Arquitectura General

El sistema implementa una arquitectura **Function Calling** que permite a un modelo de lenguaje local (Ollama) delegar tareas específicas a funciones reales del backend. En lugar de que la IA intente responder凭空, el sistema intercepta cuando el modelo decide usar una herramienta, ejecuta la función real en el servidor y devuelve el resultado para que la IA genere la respuesta final.

```
Usuario (Frontend Svelte)
    |
    v
POST /v1/chat/completions  { messages + tools }
    |
    v
FastAPI Backend
    |
    v
Ollama (modelo LLM local)  <--- recibe mensajes + tool schemas
    |
    |-- Si el modelo responde con texto --> devuelve respuesta directa
    |
    |-- Si el modelo responde con tool_calls:
    |       |
    |       v
    |   execute_tool()  -->  operaciones.py / catálogo / RAG
    |       |
    |       v
    |   Resultado real  -->  se añade como role: "tool"
    |       |
    |       v
    |   Ollama (segunda llamada)  -->  genera respuesta final con datos reales
    |       |
    |       v
    |   Respuesta conversacional al usuario
```

---

## 2. ¿Qué es Function Calling?

### Problema que resuelve

Los modelos de lenguaje (LLMs) tienen limitaciones importantes:

1. **No saben nada de tu negocio**: Un LLM genérico no conoce los precios, disponibilidad o catálogo de tu empresa.
2. **Alucinan**: Pueden inventar precios, especificaciones o disponibilidad.
3. **No tienen acceso a datos en tiempo real**: No pueden consultar una base de datos ni verificar disponibilidad de fechas.

### Solución: Function Calling

Function Calling es un protocolo donde:

1. **Defines herramientas (tools)**: Funciones reales con nombre, descripción y esquema de parámetros (JSON Schema).
2. **Las envías al LLM**: En cada petición, incluyes las definiciones de las herramientas disponibles.
3. **El LLM decide usarlas**: Si la pregunta del usuario requiere datos que el modelo no conoce, responde con un objeto estructurado `tool_calls` en lugar de texto.
4. **El backend ejecuta**: Tu servidor recibe `tool_calls`, extrae los argumentos, ejecuta la función real y devuelve el resultado.
5. **El LLM genera la respuesta final**: Con los datos reales en contexto, el modelo produce una respuesta natural y fundamentada.

### Formato OpenAI-compatible

El endpoint `/v1/chat/completions` sigue el estándar de OpenAI para function calling:

```json
// Request
{
  "messages": [
    {"role": "system", "content": "Eres un asesor de maquinaria..."},
    {"role": "user", "content": "¿Cuánto cuesta la excavadora por 5 días?"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "calcular_costo_renta",
        "description": "Calcula el costo de renta...",
        "parameters": {
          "type": "object",
          "properties": {
            "maquina": {"type": "string"},
            "dias": {"type": "integer"}
          },
          "required": ["maquina", "dias"]
        }
      }
    }
  ]
}

// Response cuando el modelo llama una herramienta
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": null,
      "tool_calls": [{
        "id": "call_abc123",
        "type": "function",
        "function": {
          "name": "calcular_costo_renta",
          "arguments": "{\"maquina\": \"Excavadora Hidráulica de Orugas\", \"dias\": 5}"
        }
      }]
    },
    "finish_reason": "tool_calls"
  }]
}

// Response final con datos ejecutados
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "La excavadora por 5 días tiene un costo de $24,937.50 MXN (precio por día: $5,250, descuento del 5%: $1,312.50)."
    },
    "finish_reason": "stop"
  }]
}
```

---

## 3. Las 14 Herramientas Disponibles

El sistema registra **14 herramientas** divididas en dos grupos:

### Grupo A: Catálogo y Consulta (7 herramientas)

| # | Herramienta | Descripción | Parámetros |
|---|---|---|---|
| 1 | **`listar_categorias`** | Obtiene todas las categorías de maquinaria con resumen | — |
| 2 | **`obtener_categoria`** | Detalle completo de una categoría | `nombre: string` |
| 3 | **`buscar_maquinaria`** | Búsqueda textual por palabra clave | `termino: string` |
| 4 | **`detalle_maquinaria`** | Ficha completa de una máquina | `nombre: string` |
| 5 | **`listar_proyectos`** | Proyectos y combinaciones frecuentes | — |
| 6 | **`obtener_proyecto`** | Maquinaria para un proyecto específico | `nombre: string` |
| 7 | **`query_maquinaria`** | Pregunta compleja al sistema RAG | `question: string`, `top_k?: int` |

### Grupo B: Operaciones de Negocio (7 herramientas)

| # | Herramienta | Qué hace | Ejemplo de uso del usuario |
|---|---|---|---|
| 8 | **`calcular_costo_renta`** | Calcula precio × días con descuentos escalonados | *"¿Cuánto cuesta la excavadora por 5 días?"* |
| 9 | **`verificar_disponibilidad`** | Consulta disponibilidad en calendario de BD | *"¿Está disponible el bulldozer el 15 de junio?"* |
| 10 | **`recomendar_por_trabajo`** | Recomienda máquinas según tipo de trabajo + presupuesto | *"Necesito maquinaria para cimentación, presupuesto $50,000"* |
| 11 | **`comparar_maquinas`** | Compara especificaciones lado a lado | *"¿Qué me conviene, orugas o ruedas?"* |
| 12 | **`calcular_costo_proyecto`** | Costo total multi-máquina con descuentos | *"Excavadora + bulldozer por una semana"* |
| 13 | **`registrar_solicitud`** | Crea solicitud de renta formal con folio | *"Quiero rentar la excavadora para el 20 de junio"* |
| 14 | **`generar_cotizacion`** | Genera cotización formal guardada en BD | *"Cotización para Constructora ARCO"* |

### Definición centralizada

Todas las herramientas se definen en `src/tools_schemas.py`:

```python
TOOL_FUNCTIONS_MAP = {
    "listar_categorias": "listar_categorias_fallback",
    "obtener_categoria": "obtener_categoria_fallback",
    "buscar_maquinaria": "buscar_maquinaria_fallback",
    "detalle_maquinaria": "detalle_maquinaria_fallback",
    "listar_proyectos": "listar_proyectos_fallback",
    "obtener_proyecto": "obtener_proyecto_fallback",
    "query_maquinaria": "query_maquinaria_backend",
    "calcular_costo_renta": "exec_calcular_costo_renta",
    "verificar_disponibilidad": "exec_verificar_disponibilidad",
    "recomendar_por_trabajo": "exec_recomendar_por_trabajo",
    "comparar_maquinas": "exec_comparar_maquinas",
    "calcular_costo_proyecto": "exec_calcular_costo_proyecto",
    "registrar_solicitud": "exec_registrar_solicitud",
    "generar_cotizacion": "exec_generar_cotizacion",
}
```

---

## 4. Arquitectura del Backend

### api.py — Endpoint `/v1/chat/completions`

Es el cerebro del function calling. Flujo interno:

```
Request { messages, tools }
    |
    v
Validar y preparar mensajes (inserta system prompt si no existe)
    |
    v
Loop (max 5 rondas de tool calling):
    |
    |-- Llamar a Ollama /api/chat  con messages + tools
    |       |
    |       |-- Si respuesta tiene tool_calls:
    |       |       |
    |       |       v
    |       |   Para cada tool_call:
    |       |       parsear arguments (JSON)
    |       |       execute_tool(nombre, args)  -->  función real
    |       |       añadir resultado como role: "tool"
    |       |       (repetir loop)
    |       |
    |       |-- Si respuesta NO tiene tool_calls:
    |               devolver response final { content }
    |
    v
Devolver ChatCompletionResponse
```

**System Prompt**: Instruye al modelo a usar herramientas para TODO lo relacionado con maquinaria, precios, disponibilidad y cotizaciones.

### src/tools_schemas.py

Define los 14 tool schemas en formato JSON Schema (OpenAI-compatible). Cada tool tiene:
- `name`: identificador único
- `description`: texto que el LLM lee para entender cuándo usar la herramienta
- `parameters`: esquema JSON con `properties` y `required`

### src/operaciones.py

Contiene las 7 funciones de negocio:

| Función | Dependencias |
|---|---|
| `calcular_costo_renta(maquina, dias, cantidad)` | `pricing.py` + `catalogo.py` |
| `verificar_disponibilidad(maquina, fecha_inicio, fecha_fin)` | PostgreSQL (`disponibilidad`) |
| `recomendar_por_trabajo(tipo_trabajo, presupuesto)` | `catalogo.py` (proyectos + categorías) |
| `comparar_maquinas(nombres)` | `catalogo.py` (especificaciones) |
| `calcular_costo_proyecto(maquinas, dias)` | `pricing.py` + `catalogo.py` |
| `registrar_solicitud(cliente, contacto, maquinas, fecha_inicio, fecha_fin)` | PostgreSQL (`solicitudes_renta`) |
| `generar_cotizacion(cliente, contacto, maquinas, dias)` | `operaciones.py` + PostgreSQL (`cotizaciones`) |

### src/pricing.py — Motor de Precios

Parsea strings de precio como `"$3,500 - $7,000 MXN/día"` y extrae rangos numéricos:

```python
parse_precio_renta("$3,500 - $7,000 MXN/día")  # → (3500.0, 7000.0)
precio_promedio("$3,500 - $7,000 MXN/día")     # → 5250.0
```

Aplica descuentos progresivos según la duración de la renta:

| Días | Descuento |
|---|---|
| 1–2 días | 0% |
| 3–6 días | 5% |
| 7–13 días | 10% |
| 14–29 días | 15% |
| 30+ días | 20% |

---

## 5. Base de Datos de Negocio

Se agregaron 3 tablas nuevas a PostgreSQL para soportar las operaciones de negocio:

### disponibilidad

```sql
CREATE TABLE disponibilidad (
    id SERIAL PRIMARY KEY,
    maquina_id INTEGER REFERENCES maquinas(id),
    fecha DATE NOT NULL,
    disponible BOOLEAN DEFAULT TRUE,
    notas TEXT DEFAULT '',
    UNIQUE(maquina_id, fecha)
);
```

Almacena el calendario de disponibilidad por máquina y fecha. El seed genera ~500 registros para los meses de junio a septiembre 2026 con patrones realistas:

- Máquinas de alta demanda (Excavadora, Retroexcavadora, Bulldozer): ~55% de ocupación
- Máquinas de media demanda (Motoniveladora, Grúa, Generador): ~25% de ocupación
- Máquinas de nicho (Robot de Demolición, Perforadora): ~10% de ocupación

### solicitudes_renta

```sql
CREATE TABLE solicitudes_renta (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(20) UNIQUE NOT NULL,
    cliente VARCHAR(255), contacto VARCHAR(255),
    maquinas JSONB,  -- [{"nombre": "...", "cantidad": N}]
    fecha_inicio DATE, fecha_fin DATE,
    estado VARCHAR(50) DEFAULT 'pendiente',
    notas TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### cotizaciones

```sql
CREATE TABLE cotizaciones (
    id SERIAL PRIMARY KEY,
    folio VARCHAR(20) UNIQUE NOT NULL,
    cliente VARCHAR(255), contacto VARCHAR(255),
    maquinas JSONB,  -- [{"nombre": "...", "cantidad": N, "precio_unitario": N, "subtotal": N}]
    dias INTEGER,
    subtotal NUMERIC(12,2),
    descuento NUMERIC(12,2) DEFAULT 0,
    total NUMERIC(12,2),
    valida_hasta DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Datos semi-reales incluidos

El script `db/seed_business.py` inserta:

| Tabla | Registros | Detalle |
|---|---|---|
| `disponibilidad` | ~4,000 | 34 máquinas × 118 días (Jun–Sep 2026) |
| `solicitudes_renta` | 10 | Clientes realistas: Constructora ARCO, Conagua, Municipalidad de León, etc. |
| `cotizaciones` | 6 | Folios COT-2026-001 al 006 con montos, descuentos y fechas de validez |

---

## 6. Lógica de Precios y Descuentos

### Extracción de precio

Los precios en el catálogo están en formato texto: `"$3,500 - $7,000 MXN/día"`. El sistema:

1. **Extrae el rango numérico** con regex: `\$?([\d,]+)\s*-\s*\$?([\d,]+)`
2. **Calcula el precio promedio**: `(min + max) / 2`
3. **Aplica descuento progresivo** según días
4. **Calcula subtotal y total**

### Ejemplo: Excavadora por 5 días

```
precio_str = "$3,500 - $7,000 MXN/día"
precio_promedio = (3500 + 7000) / 2 = 5,250/día

subtotal = 5,250 × 5 días = $26,250
descuento (5%) = $1,312.50
total = $24,937.50
```

### Ejemplo: Excavadora x2 por 7 días

```
precio_promedio = 5,250/día

subtotal = 5,250 × 7 días × 2 unidades = $73,500
descuento (10%) = $7,350
total = $66,150
```

---

## 7. Frontend Svelte

### Estructura

```
frontend/
├── package.json                  # Dependencias: svelte + vite
├── vite.config.js                # Proxy: /v1 y /api → backend
├── svelte.config.js
├── index.html
├── nginx.conf                    # Proxy reverso en producción
├── Dockerfile                    # Multi-stage build
├── src/
│   ├── main.js                   # Entry point
│   ├── App.svelte                # Componente raíz
│   ├── app.css                   # Estilos globales (tema oscuro)
│   └── lib/
│       ├── Chat.svelte           # Ventana de chat completa
│       ├── Message.svelte        # Burbuja de mensaje individual
│       ├── ToolCall.svelte       # Visualización de tool_calls colapsable
│       └── api.js                # Cliente HTTP para /v1/chat/completions
```

### Componentes

**Chat.svelte**: El componente principal. Mantiene el estado del chat, maneja el envío de mensajes, llama a la API con el protocolo de function calling y renderiza la conversación. Envía siempre los tool schemas al backend.

**Message.svelte**: Renderiza cada mensaje diferenciando por rol:
- `user`: burbuja azul alineada a la derecha
- `assistant`: burbuja gris alineada a la izquierda
- `tool`: burbuja pequeña con información de la herramienta ejecutada

**ToolCall.svelte**: Muestra una tarjeta colapsable con el nombre de la herramienta y sus argumentos. Al hacer clic se expande para ver los detalles completos del JSON.

### Flujo del frontend

```
Usuario escribe: "¿Cuánto cuesta la excavadora por 5 días?"
    |
    v
Frontend envía POST /v1/chat/completions con:
  - messages: [{role: "user", content: "¿Cuánto cuesta...?"}]
  - tools: [definiciones de las 14 herramientas]
    |
    v
Backend devuelve CHOICE 1 (tool_calls):
  - assistant: tool_calls = [{name: "calcular_costo_renta", arguments: {...}}]
    |
    v
Frontend reenvía con tool results:
  - messages: [
      {role: "user", ...},
      {role: "assistant", tool_calls: [...]},
      {role: "tool", name: "calcular_costo_renta", content: "{...}"}
    ]
    |
    v
Backend devuelve CHOICE 2 (respuesta final):
  - assistant: "La excavadora por 5 días cuesta $24,937.50 MXN..."
    |
    v
Frontend muestra la respuesta al usuario
```

---

## 8. Flujo Completo de una Consulta

### Ejemplo real: "Necesito maquinaria para cimentación, presupuesto $50,000"

```
Paso 1: Usuario escribe en frontend
    |
Paso 2: Frontend envía a POST /v1/chat/completions
    |
Paso 3: Ollama recibe messages + tools.
        El LLM lee la descripción de "recomendar_por_trabajo"
        y decide usarla porque requiere consultar datos reales.
    |
Paso 4: Backend recibe tool_calls:
        tool_calls[0].function = {
            name: "recomendar_por_trabajo",
            arguments: '{"tipo_trabajo": "cimentación", "presupuesto": 50000}'
        }
    |
Paso 5: execute_tool() llama a operaciones.recomendar_por_trabajo()
        → busca proyectos con "cimentación"
        → encuentra "Excavación de Cimentación en Casa con Acceso Estrecho"
        → extrae 5 máquinas recomendadas con precios
        → calcula costo total vs presupuesto
    |
Paso 6: Backend añade resultado como role: "tool" y reenvía a Ollama
    |
Paso 7: Ollama genera respuesta final:
        "Para excavación de cimentación, te recomiendo:
         - Miniexcavadora ultrarreducida: $900-$1,800/día
         - Apisonador manual: $300-$800/día
         - Carretilla motorizada: $500-$1,200/día
         Con tu presupuesto de $50,000 podrías rentar el
         equipo completo por aproximadamente 12 días."
    |
Paso 8: Frontend muestra la respuesta al usuario
```

### Diagrama de secuencia

```
Frontend              Backend (FastAPI)            Ollama              PostgreSQL
   |                       |                         |                     |
   |-- POST /v1/chat ----->|                         |                     |
   |                       |-- /api/chat  ---------->|                     |
   |                       |   (messages + tools)    |                     |
   |                       |                         |                     |
   |                       |<---- tool_calls --------|                     |
   |                       |                         |                     |
   |                       |-- execute_tool() -------|-------------------->|
   |                       |   (SQL query)           |                     |
   |                       |<---- datos reales ------|---------------------|
   |                       |                         |                     |
   |                       |-- /api/chat  ---------->|                     |
   |                       |   (messages + tool      |                     |
   |                       |    results)              |                     |
   |                       |                         |                     |
   |                       |<---- respuesta text ----|                     |
   |                       |                         |                     |
   |<-- choice: content ---|                         |                     |
   |                       |                         |                     |
```

---

## 9. Docker y Despliegue

### Servicios

| Servicio | Puerto | Imagen | Propósito |
|---|---|---|---|
| `ollama` | 11435 | `ollama/ollama:latest` | Modelos de lenguaje local |
| `postgres` | 5432 | `postgres:16-alpine` | Base de datos del catálogo y negocio |
| `backend` | 8000 | build `.` | FastAPI con function calling |
| `frontend` | 5173 | build `./frontend` | Svelte + Nginx |

### Comandos

```bash
# 1. Levantar todo
docker compose up -d

# 2. Descargar modelos
docker exec ollama ollama pull qwen2.5:7b
docker exec ollama ollama pull nomic-embed-text

# 3. Poblar datos de negocio
docker exec rag_backend python db/seed_business.py

# 4. Abrir frontend
# http://localhost:5173

# 5. Ver logs del backend
docker compose logs -f backend

# 6. Probar function calling directo
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Cuanto cuesta la excavadora por 5 dias?"}
    ]
  }' | python -m json.tool
```

---

## 10. Ejemplos de Uso

### 1. Consulta de costo

```bash
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Cuanto cuesta la excavadora por 5 dias?"}]
  }' | python -m json.tool

# Respuesta esperada (después de tool_calls + ejecución):
# "La excavadora por 5 días tiene un costo de $24,937.50 MXN
#  ($5,250/día, descuento del 5%: $1,312.50)"
```

### 2. Verificar disponibilidad

```bash
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Esta disponible el bulldozer del 15 al 20 de junio?"}]
  }' | python -m json.tool
```

### 3. Recomendación por trabajo

```bash
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Necesito maquinaria para cimentacion, presupuesto 50000"}]
  }' | python -m json.tool
```

### 4. Comparar máquinas

```bash
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Que me conviene mas, excavadora de orugas o miniexcavadora?"}]
  }' | python -m json.tool
```

### 5. Cotización formal

```bash
curl -s -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Genera una cotizacion para Constructora ARCO, contacto carlos@arco.com, para rentar una excavadora por 7 dias"}]
  }' | python -m json.tool
```

### 6. Obtener herramientas disponibles

```bash
curl -s http://localhost:8000/v1/tools | python -m json.tool | head -40
```

---

## 11. Justificación de Tecnologías

### ¿Por qué FastAPI para function calling?

| Factor | FastAPI | Alternativa (Flask) |
|---|---|---|
| **Validación automática** | Pydantic models validan request/response | Requiere validación manual |
| **Documentación** | Swagger/OpenAPI automático en `/docs` | Requiere flasgger |
| **Rendimiento** | Asíncrono por defecto (uvicorn) | Síncrono, más lento |
| **Tipado** | Type hints nativos con Pydantic | Sin tipo nativo |

### ¿Por qué un solo endpoint `/v1/chat/completions`?

En lugar de crear un endpoint para cada función (como los endpoints REST tradicionales en `/api/maquinaria`, `/api/proyectos`, etc.), el function calling unifica todo en un solo endpoint. La IA decide qué herramienta usar según la intención del usuario. Esto:

1. **Simplifica el frontend**: Solo necesita conocer un endpoint
2. **Hace el sistema extensible**: Agregar una nueva herramienta no requiere cambios en el frontend
3. **Sigue el estándar OpenAI**: Cualquier cliente compatible con OpenAI puede usar este backend

### ¿Por qué ejecutar tools en el backend y no en el frontend?

| Enfoque | Ventaja | Desventaja |
|---|---|---|
| **Ejecutar en backend** (elegido) | Un solo request del frontend; el backend hace el loop completo | Mayor latencia en el backend |
| **Ejecutar en frontend** | Frontend más interactivo | Frontend debe conocer todas las APIs; múltiples requests |

El backend ejecuta las tools automáticamente: recibe el mensaje, llama a Ollama, si hay `tool_calls` las ejecuta, reenvía a Ollama y devuelve la respuesta final. El frontend solo hace **una** llamada.

### ¿Por qué Svelte y no React/Vue?

| Factor | Svelte | React | Vue |
|---|---|---|---|
| **Bundle size** | ~13 KB gzip | ~45 KB gzip | ~33 KB gzip |
| **Curva de aprendizaje** | Baja (JavaScript vanilla) | Media (JSX) | Media |
| **Rendimiento** | Sin virtual DOM | Virtual DOM | Virtual DOM |
| **Compilación** | Compila, no interpreta | Interpreta en runtime | Compila parcialmente |

Svelte genera el bundle más pequeño (~13 KB), ideal para un contenedor Docker donde el tamaño importa.

---

## 12. Glosario

| Término | Significado |
|---|---|
| **Function Calling** | Protocolo donde el LLM decide llamar funciones reales en lugar de responder directamente |
| **Tool / Herramienta** | Función definida con nombre, descripción y esquema JSON que el LLM puede invocar |
| **Tool Schema** | Definición JSON de una herramienta siguiendo JSON Schema |
| **Tool Call** | Invocación estructurada que el LLM devuelve: `{name, arguments}` |
| **Tool Choice** | Control de qué herramientas puede usar el LLM (`"auto"`, `"none"`, o forzar una) |
| **System Prompt** | Instrucción inicial que define el comportamiento del asistente |
| **Role: tool** | Rol en los mensajes que indica que el contenido es el resultado de una herramienta ejecutada |
| **OpenAI-compatible** | API que sigue el mismo formato que OpenAI `/v1/chat/completions` |
| **Token** | Unidad de texto que el modelo procesa (~0.75 palabras) |
| **Descuento escalonado** | Descuento que aumenta según la duración de la renta (5%, 10%, 15%, 20%) |
| **Folio** | Identificador único de solicitud o cotización (ej: SOL-2026-A1B2C3) |
| **Seed data** | Datos de prueba semi-reales para poblar la base de datos |
| **LLM** | Large Language Model - Modelo de lenguaje grande |
| **RAG** | Retrieval-Augmented Generation - Búsqueda + Generación |

---

*Documentación de la FASE 3: Implementación de Llamadas a Función (Function Calling).*
*Junio 2026 — Sistema RAG de Renta de Maquinaria Pesada con Ollama.*
