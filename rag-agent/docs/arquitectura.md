# Documentacion del Sistema RAG con Base de Datos Vectorial

## Indice

1. [Arquitectura General](#1-arquitectura-general)
2. [Docker Compose y Ollama](#2-docker-compose-y-ollama)
3. [Modelos de IA](#3-modelos-de-ia)
4. [Estructura del Proyecto](#4-estructura-del-proyecto)
5. [Archivos Python en Detalle](#5-archivos-python-en-detalle)
6. [Conceptos Clave](#6-conceptos-clave)
7. [Flujo de Funcionamiento](#7-flujo-de-funcionamiento)
8. [Comandos de Uso](#8-comandos-de-uso)
9. [Almacenamiento Vectorial (ChromaDB)](#9-almacenamiento-vectorial-chromadb)
10. [Justificacion de Tecnologias](#10-justificacion-de-tecnologias)

---

## 1. Arquitectura General

El sistema implementa una arquitectura **RAG (Retrieval-Augmented Generation)** que permite hacer preguntas sobre documentos y obtener respuestas generadas por una IA local, fundamentadas únicamente en la informacion recuperada de los documentos.

```
Documento (PDF/HTML/TXT)
    |
    v
DocumentLoader  (lectura del archivo)
    |
    v
TextChunker     (fragmentacion en trozos)
    |
    v
OllamaClient    (genera embeddings vectoriales)
    |
    v
VectorStore     (almacena en ChromaDB)
    |
    v   (cuando el usuario consulta)
    |
Consulta  -->  OllamaClient (embedding de la pregunta)
    |
    v
VectorStore     (busqueda semantica Top-K)
    |
    v
ReRanker        (reordena por relevancia con IA)
    |
    v
OllamaClient    (genera respuesta con contexto)
    |
    v
RAGMetrics      (evalua precision, recall, fidelidad)
```

---

## 2. Docker Compose y Ollama

### docker-compose.yml

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
    restart: unless-stopped

volumes:
  ollama_data:
```

**Explicacion:**

- **image: ollama/ollama:latest**: Usa la imagen oficial de Ollama. Ollama es un servidor que permite ejecutar modelos de lenguaje (LLMs) localmente, sin necesidad de internet ni servicios en la nube.
- **container_name: ollama**: El contenedor se llama "ollama" para referenciarlo facilmente.
- **ports: "11435:11434"**: Mapea el puerto 11435 del host al 11434 del contenedor. La API de Ollama vive en el puerto 11434 por defecto. Se usa 11435 en el host para no conflictuar con otra instalacion de Ollama.
- **volumes: ollama_data:/root/.ollama**: Los modelos descargados se guardan en un volumen persistente. Si el contenedor se elimina y recrea, los modelos no se descargan de nuevo.
- **OLLAMA_HOST=0.0.0.0**: Obliga a Ollama a escuchar en todas las interfaces de red (no solo localhost).
- **restart: unless-stopped**: El contenedor se reinicia automaticamente si falla o si se reinicia el sistema.

### Comandos basicos de Docker

```bash
# Iniciar Ollama
sudo docker compose up -d

# Verificar que esta corriendo
sudo docker ps

# Ver logs
sudo docker logs ollama

# Detener
sudo docker compose down

# Ejecutar comandos dentro del contenedor
sudo docker exec ollama ollama list
sudo docker exec ollama ollama pull qwen2.5:3b
```

---

## 3. Modelos de IA

### Que es un modelo de IA/local

Un modelo de lenguaje (LLM) es un programa entrenado con millones de textos que puede entender y generar lenguaje humano. Ejecutarlos localmente significa que todo corre en tu maquina, sin enviar datos a servidores externos.

### Modelos en este proyecto

| Modelo | Proposito | Tamano |
|---|---|---|
| **qwen2.5:3b** | Generacion de respuestas y re-ranking | 1.9 GB |
| **nomic-embed-text** | Generacion de embeddings (vectores) | 274 MB |

**qwen2.5:3b**: Modelo de 3 mil millones de parametros de Alibaba. Corre en CPU. Se usa para:
1. **Generar respuestas**: Recibe el contexto recuperado + la pregunta y produce la respuesta.
2. **Re-ranking**: Vuelve a evaluar cada fragmento recuperado para reordenarlos por relevancia.

**nomic-embed-text**: Modelo especializado en convertir texto en vectores numericos (embeddings). Es pequeno y rapido. Se usa para:
1. Convertir fragmentos de documentos en vectores para almacenarlos.
2. Convertir la pregunta del usuario en vector para buscar fragmentos similares.

### Por que dos modelos

En RAG se necesitan dos capacidades distintas:
- **Embeddings**: Transformar texto en numeros para busqueda semantica (nomic-embed-text).
- **Generacion**: Producir respuestas en lenguaje natural (qwen2.5:3b).

Usar el mismo modelo para ambas cosas seria ineficiente. Los modelos de embeddings son pequenos y rapidos; los de generacion son mas grandes y lentos.

---

## 4. Estructura del Proyecto

```
.ai/
├── config.py                  # Configuracion centralizada
├── main.py                    # Punto de entrada (CLI)
├── requirements.txt           # Dependencias Python
├── docker-compose.yml         # Orquestacion Docker
├── Documentacion.md           # Este documento
├── requerimientos.md          # Requisitos del proyecto
├── README.md
├── src/
│   ├── document_loader.py     # Lectura de PDF/HTML/TXT
│   ├── text_chunker.py        # Fragmentacion de texto
│   ├── ollama_client.py       # Comunicacion con Ollama API
│   ├── vector_store.py        # Interfaz con ChromaDB
│   ├── reranker.py            # Reordenamiento por relevancia
│   ├── rag_metrics.py         # Evaluacion RAGAS
│   └── rag.py                 # Orquestador del sistema RAG
├── chroma_db/                 # Base de datos vectorial persistente
└── Documentos/                # Documentos a ingestar
```

---

## 5. Archivos Python en Detalle

### config.py

Configuracion centralizada usando variables de entorno con valores por defecto:

```python
OLLAMA_BASE_URL = "http://localhost:11435"  # Donde corre Ollama
OLLAMA_MODEL = "qwen2.5:3b"                 # Modelo para generar respuestas
EMBEDDING_MODEL = "nomic-embed-text"         # Modelo para embeddings
CHROMA_PERSIST_DIR = "./chroma_db"           # Donde guardar la BD vectorial
CHUNK_SIZE = 512                             # Tamanio de cada fragmento
CHUNK_OVERLAP = 128                          # Solapamiento entre fragmentos
TOP_K = 10                                   # Cuantos fragmentos recuperar
SIMILARITY_METRIC = "cosine"                 # Metrica de similitud
RERANK_ENABLED = True                        # Activar re-ranking
RERANK_TOP_N = 5                             # Fragmentos finales tras re-rank
ENABLE_METRICS = True                        # Evaluar respuestas
COLLECTION_NAME = "rag_knowledge_base"       # Nombre de la coleccion
```

### main.py

Punto de entrada con interfaz de linea de comandos (CLI). Usa `argparse` para definir comandos:

- **`ingest <archivo>`**: Procesa un documento y lo almacena en la BD vectorial.
- **`query <pregunta>`**: Hace una pregunta al sistema RAG.
- **`stats`**: Muestra estadisticas de la base de datos.
- **`quality <pregunta>`**: Evalua la calidad de recuperacion.

### src/document_loader.py

Lee archivos de distintos formatos y extrae su texto:

- **PDF**: Usa `pypdf` (PdfReader) para extraer texto pagina por pagina.
- **HTML**: Usa `BeautifulSoup` para parsear el HTML y obtener solo el texto.
- **TXT**: Lectura directa del archivo.

### src/text_chunker.py

Divide el texto en fragmentos (chunks) para su procesamiento. Implementa:

1. **Limpieza**: Normaliza espacios, elimina caracteres especiales.
2. **Division por parrafos**: Usa dobles saltos de linea como separadores.
3. **Fragmentacion**: Combina parrafos respetando el tamanio maximo (`chunk_size`).
4. **Solapamiento (overlap)**: Mantiene contexto entre fragmentos consecutivos repitiendo las ultimas palabras del chunk anterior.

**Por que fragmentar**: Los modelos de embeddings y LLMs tienen limites de contexto. Un documento completo puede tener miles de palabras. Dividirlo en trozos permite:
- Procesar documentos grandes.
- Recuperar solo las partes relevantes a la pregunta.
- Mantener la busqueda eficiente.

### src/ollama_client.py

Cliente HTTP para comunicarse con la API de Ollama. Dos funciones principales:

**get_embeddings(textos)**: Envia textos al modelo de embeddings y devuelve vectores numericos.

```python
POST /api/embeddings
Body: {"model": "nomic-embed-text", "prompt": "texto"}
Response: {"embedding": [0.45, 0.12, ...]}  # 768 numeros
```

**generate(pregunta, contexto)**: Envia la pregunta + contexto al modelo de generacion y devuelve la respuesta.

```python
POST /api/generate
Body: {
    "model": "qwen2.5:3b",
    "prompt": "Contexto:\n...\n\nPregunta: ...\n\nRespuesta:",
    "system": "Eres un asistente...",
    "stream": false
}
Response: {"response": "La respuesta generada"}
```

### src/vector_store.py

Interfaz con **ChromaDB**, la base de datos vectorial. Usa `chromadb.PersistentClient` para guardar datos en disco.

**Funciones**:
- **add_documents**: Almacena IDs + embeddings + textos + metadatos.
- **search**: Busca los K textos mas similares a un embedding dado.
- **search_with_scores**: Igual que search pero devuelve con puntuaciones.
- **count**: Numero de documentos almacenados.
- **delete_collection**: Elimina toda la coleccion.

La metrica de similitud se configura al crear la coleccion:
- `cosine` = similitud del coseno (por defecto)
- `l2` = distancia euclidiana
- `ip` = producto punto

### src/reranker.py

Reordena los fragmentos recuperados usando el LLM para evaluar su relevancia con la pregunta. Esto mejora la calidad porque:
1. La busqueda vectorial encuentra fragmentos semanticamente cercanos.
2. El re-ranking usa el LLM para leer cada fragmento y la pregunta, y puntuar que tan relevante es realmente.
3. Los fragmentos mejor puntuados se usan como contexto final.

Tambien incluye `ReciprocalRankFusion` que combina resultados de multiples busquedas.

### src/rag_metrics.py

Implementa las 4 metricas del marco **RAGAS** (RAG Assessment):

1. **Context Precision (MT-01)**: Que tan precisos son los fragmentos recuperados.
2. **Context Recall (MT-02)**: Que tan completa es la informacion recuperada.
3. **Faithfulness (MT-03)**: Si la respuesta se fundamenta solo en el contexto (sin alucinaciones).
4. **Answer Relevancy (MT-04)**: Si la respuesta responde directamente a la pregunta.

Cada metrica evalua usando el mismo LLM (qwen2.5:3b) con un prompt especifico que le pide puntuar de 0 a 1.

### src/rag.py

Orquestador que conecta todos los componentes:

**ingest_document(file_path, metadata)**:
1. Carga el documento con `DocumentLoader`
2. Fragmenta con `TextChunker`
3. Genera embeddings con `OllamaClient`
4. Almacena en `VectorStore`

**query(question, top_k)**:
1. Genera embedding de la pregunta
2. Busca en `VectorStore` (recupera top_k * 2)
3. Reordena con `ReRanker` (opcional)
4. Llama al LLM con el contexto para generar respuesta
5. Evalua metricas (opcional)
6. Devuelve respuesta + fuentes + metricas + latencia

---

## 6. Conceptos Clave

### ?Que es un Embedding?

Un **embedding** es una representacion numerica de un texto en forma de vector (lista de numeros). Por ejemplo, la frase "Hola mundo" podria convertirse en:

```
[0.45, 0.12, -0.78, 0.33, ..., 0.91]  (768 numeros)
```

La magia es que textos con significado similar quedan cerca en el espacio vectorial. "Gato" y "Felino" generan vectores cercanos; "Gato" y "Tornillo" generan vectores lejanos. Esto permite buscar por **significado** y no solo por palabras exactas.

### ?Que es Chunking?

**Chunking** (fragmentacion) es dividir un documento grande en trozos mas pequenos. Es necesario porque:

- Los modelos de embeddings tienen limite de tokens (nomic-embed-text acepta ~2048 tokens).
- Los LLMs tienen contexto limitado (qwen2.5:3b acepta ~32768 tokens, pero es lento con contextos grandes).
- La busqueda es mas precisa cuando se recuperan solo los fragmentos relevantes.

**Parametros de chunking**:
- `chunk_size = 512`: Cada fragmento tendra ~512 caracteres.
- `chunk_overlap = 128`: Entre fragmentos consecutivos se repiten ~128 caracteres para no perder contexto.
- **Solapamiento (overlap)**: Si la pregunta abarca el final del chunk 1 y el inicio del chunk 2, el overlap asegura que ambos fragmentos contengan esa informacion.

### ?Que es una Base de Datos Vectorial?

Una base de datos vectorial almacena vectores (embeddings) y permite buscar los mas similares a un vector de consulta. Es diferente a una BD tradicional que busca por coincidencias exactas en texto.

### ?Por que ChromaDB?

ChromaDB se eligio porque:
1. **Embebida**: No necesita servidor separado, corre como libreria Python.
2. **Persistente**: Guarda datos en disco (a diferencia de solo en memoria).
3. **Simple**: API minimalista, ideal para prototipado rapido.
4. **Soporta metadatos**: Permite filtrar por categoria, autor, etc.
5. **Compatible**: Funciona con cualquier modelo de embeddings.

Alternativas consideradas:
| BD | Ventaja | Desventaja |
|---|---|---|
| **ChromaDB** | No necesita servidor, facil | Menos escalable |
| **Qdrant** | Alto rendimiento, filtros complejos | Requiere servidor |
| **pgvector** | Integracion con PostgreSQL | Requiere PostgreSQL |
| **LanceDB** | Serverless, sin procesos | Menos madura |

### ?Que es RAG?

RAG (Retrieval-Augmented Generation) es un patron arquitectonico que combina:
1. **Recuperacion (Retrieval)**: Buscar informacion relevante en una base de conocimiento.
2. **Generacion (Generation)**: Usar un LLM para redactar una respuesta fundamentada en esa informacion.

La ventaja frente a usar solo un LLM:
- El LLM no siempre sabe la respuesta (no fue entrenado con tus documentos).
- El LLM puede alucinar (inventar respuestas).
- Con RAG, el LLM solo responde con informacion que recuperaste, reduciendo alucinaciones.

---

## 7. Flujo de Funcionamiento

### Ingesta de un documento

```
Archivo PDF  -->  DocumentLoader.load()  -->  texto plano
                                                    |
                                                    v
                                           TextChunker.chunk()
                                                    |
                                           [chunk1, chunk2, ...]
                                                    |
                                                    v
                                           OllamaClient.get_embeddings()
                                                    |
                                           [[0.1, 0.2, ...], [0.3, 0.4, ...]]
                                                    |
                                                    v
                                           VectorStore.add_documents()
                                                    |
                                                    v
                                           chroma_db/ (disco)
```

### Consulta (query)

```
Pregunta: "Cual es el paso 1?"
     |
     v
OllamaClient.get_embeddings([pregunta])
     |
     v
VectorStore.search(embedding_pregunta, top_k=20)
     |
     v
[20 fragmentos mas similares]
     |
     v
ReRanker.rerank(pregunta, fragmentos)
     |
     v
[5 fragmentos reordenados por relevancia]
     |
     v
OllamaClient.generate(pregunta, contexto)
     |
     v
"El paso 1 es Ingesta de Documentos..."
     |
     v
RAGMetrics.evaluate()  (opcional)
     |
     v
Respuesta + fuentes + metricas + latencia
```

---

## 8. Comandos de Uso

```bash
# 1. Iniciar Ollama (si no esta corriendo)
sudo docker compose up -d

# 2. Verificar modelos disponibles
sudo docker exec ollama ollama list

# 3. Ingestar un documento PDF
python main.py ingest Documentos/mi_archivo.pdf --metadata categoria=manual autor=damaya

# 4. Hacer una pregunta (sin re-ranking para rapidez)
python main.py query "Cual es el contenido" --no-rerank --no-metrics

# 5. Hacer una pregunta con re-ranking y metricas (mas lento)
python main.py query "Cual es el paso 1"

# 6. Ver estadisticas de la base
python main.py stats

# 7. Evaluar calidad de recuperacion
python main.py quality "Cual es el paso 1"

# 8. Cambiar metrica de similitud
python main.py --metric euclidean query "pregunta"

# 9. Eliminar la base de datos (reingestar desde cero)
rm -rf chroma_db/
```

### Parametros del comando query

| Parametro | Descripcion |
|---|---|
| `--no-rerank` | Desactiva re-ranking (mas rapido, menos preciso) |
| `--no-metrics` | Desactiva evaluacion RAGAS (mas rapido) |
| `--top-k N` | Cambia cuantos fragmentos recuperar (defecto: 10) |
| `--ground-truth "..."` | Respuesta esperada para comparar metricas |

### Salida del comando query

```
RESPUESTA
- Claude
- Gemini
- ChatGPT

Total: 53509 ms  |  Busqueda: 16 ms  |  Generacion: 29713 ms

METRICAS RAG
  MT-01 Context Precision:  0.800
  MT-02 Context Recall:     1.000
  MT-03 Faithfulness:       0.900
  MT-04 Answer Relevancy:   0.800

FUENTES RECUPERADAS (Top-5)
[1] [score: 0.700]
  IAs Locales y Cloud: Comparativa de Modelos...
```

La latencia de **busqueda (< 16 ms)** cumple la meta de la rubrica (< 100 ms).
La latencia de **generacion** depende del modelo (qwen2.5:3b en CPU: ~20-50 segs).

---

## 9. Almacenamiento Vectorial (ChromaDB)

### Estructura en disco

```
chroma_db/
├── chroma.sqlite3          (404 KB)  -- indice SQLite con metadatos
└── 4d1ed590-.../                      (carpeta de la coleccion)
    ├── header.bin           (0.1 KB) -- metadatos del indice HNSW
    ├── data_level0.bin     (313 KB)  -- datos de los vectores (embeddings)
    ├── length.bin           (0.4 KB) -- tamanio de cada vector
    └── link_lists.bin       (0.0 KB) -- lista de vecinos (grafo HNSW)
```

### Como se almacena cada fragmento

Para cada fragmento, ChromaDB guarda:

| Campo | Descripcion | Ejemplo |
|---|---|---|
| **ID** | UUID unico | `9205acea-c7e6-4218-b113-9e6b7aee1b77` |
| **Embedding** | Vector de 768 numeros | `[0.45, 0.25, -2.71, ...]` |
| **Document** | Texto del fragmento | `"Guia de Implementacion..."` |
| **Metadata** | Datos adicionales | `{"autor": "damaya", "categoria": "tarea"}` |

### Indice HNSW (Indexacion)

ChromaDB usa el algoritmo **HNSW (Hierarchical Navigable Small World)** para busqueda aproximada de vecinos cercanos. Es como tener un mapa de carreteras entre vectores: para encontrar los mas cercanos a una consulta, navega por este grafo en lugar de comparar contra todos uno por uno.

**Parametros de indexacion configurados:**

| Parametro | Valor | Que hace |
|---|---|---|
| `hnsw:space` | `cosine` | Metrica de distancia (cosine, l2, ip) |
| `hnsw:M` | `32` | Maximo de conexiones por nodo. Mayor = mas precision, mas memoria |
| `hnsw:construction_ef` | `200` | Tamano de la busqueda durante la construccion del indice. Mayor = mejor calidad, construccion mas lenta |
| `hnsw:search_ef` (default) | `10` | Tamano de la busqueda durante consulta. Controla velocidad vs precision |

**Efecto en la rubrica:**

- Con `M=32` y `construction_ef=200`, el indice prioriza **precision de recuperacion** sobre velocidad de construccion.
- Las busquedas en el grafo HNSW toman **< 16 ms** con 5-21 documentos, muy por debajo del limite de 100 ms que exige la rubrica.
- Para colecciones grandes (miles de documentos), estos parametros mantienen el recall > 90% con latencias estables.

### Persistencia

A diferencia de bases en memoria, ChromaDB con `PersistentClient` guarda todo en disco. Si apagas el sistema y lo vuelves a encender, los datos siguen ahi.

### Colecciones

Una coleccion agrupa documentos relacionados. En este proyecto se usa la coleccion `rag_knowledge_base`. Se pueden tener multiples colecciones para diferentes temas o proyectos.

---

## 10. Justificacion de Tecnologias

### Hardware disponible

```
CPU: AMD Ryzen 5 5625U (6 nucleos, 12 hilos)
RAM: 9.6 GB
GPU: No tiene GPU dedicada (solo graficos integrados Radeon)
SO:  Fedora Linux
```

Todas las decisiones tecnologicas estan condicionadas por este hardware: **CPU-only, sin GPU, 9.6 GB de RAM**.

### Por que Ollama y no LM Studio

| Factor | Ollama | LM Studio |
|---|---|---|
| **Arquitectura** | Cliente-servidor (API HTTP) | App de escritorio con GUI |
| **Integracion** | API sencilla para integrar desde Python | Disenado para uso interactivo manual |
| **Docker** | Corre en contenedor Docker, limpio | App con dependencias de escritorio |
| **Linea de comandos** | Soporte nativo para scripting | Mas limitado en CLI |
| **Consumo** | Servicio ligero en segundo plano | App grafica con overhead |

**Decision**: Ollama porque es headless (sin interfaz grafica), expone una API HTTP limpia para integrar desde Python, y corre en Docker sin contaminar el sistema. LM Studio esta pensado para chat manual, no para integrarse en un pipeline automatico.

### Por que qwen2.5:3b y no otro modelo

Opciones consideradas para el modelo de generacion:

| Modelo | Parametros | Tamano | RAM necesaria | Viable en CPU |
|---|---|---|---|---|
| **qwen2.5:3b** | 3B | 1.9 GB | ~4 GB | Si |
| qwen2.5:7b | 7B | 4.5 GB | ~8 GB | Limitado (ocupa casi toda la RAM) |
| llama3.2:3b | 3B | 2.0 GB | ~4 GB | Si |
| gemma3:4b | 4B | 2.6 GB | ~5 GB | Si |
| llama2:7b | 7B | 3.8 GB | ~8 GB | Limitado |
| mistral:7b | 7B | 4.1 GB | ~8 GB | Pesa demasiado |

**Decision**: qwen2.5:3b tiene 3B parametros, pesa 1.9 GB, y deja suficiente RAM libre (9.6 - 1.9 - 0.274 = ~7.4 GB) para que el sistema operativo, Docker, ChromaDB y el resto del pipeline funcionen sin swap. Un modelo de 7B ocuparia ~4+ GB y dejaria el sistema al limite. Ademas, qwen2.5 fue entrenado con datos multilingue incluyendo espanol, lo que mejora la calidad de respuestas en este idioma comparado con modelos como llama3.

### Por que nomic-embed-text y no otro embedding

| Modelo | Dimensiones | Tamano | Uso en CPU |
|---|---|---|---|
| **nomic-embed-text** | 768 | 274 MB | Rapido |
| all-minilm | 384 | 132 MB | Muy rapido pero menos preciso |
| bge-small-en | 384 | 136 MB | Similar a all-minilm |
| bge-m3 | 1024 | 458 MB | Mas pesado, mejor en multilingue |

**Decision**: nomic-embed-text ofrece el mejor equilibrio entre tamano (274 MB), calidad de embeddings (768 dimensiones) y velocidad en CPU. all-minilm es mas rapido pero captura peor el significado. bge-m3 es mejor en multilingue pero pesa casi el doble. nomic-embed-text funciona bien con espanol y su limite de 2048 tokens por fragmento es suficiente para chunks de 512 caracteres.

### Por que ChromaDB y no Qdrant/pgvector/LanceDB

| Base | Tipo | Requisito | Persistencia | Ideal para |
|---|---|---|---|---|
| **ChromaDB** | Libreria embebida | Solo Python | Si (disco) | Prototipado, proyectos pequenos |
| Qdrant | Servidor independiente | Docker + Puerto extra | Si | Alta concurrencia, produccion |
| pgvector | Extension de PostgreSQL | PostgreSQL funcionando | Si | Ya usas PostgreSQL |
| LanceDB | Serverless embebido | Solo Python | Si | Escalabilidad futura |

**Decision**: ChromaDB se eligio porque:

1. **No necesita servidor**: Se instala con `pip install chromadb` y ya funciona. Qdrant requiere otro contenedor Docker, otro puerto, otra configuracion. En un proyecto de prototipado con RAM limitada, menos servicios corriendo = mejor.
2. **API simple**: Con 4 funciones (add, search, count, delete) tienes el sistema completo.
3. **Persistente**: Guarda en disco, los datos sobreviven reinicios.
4. **Embedding-agnostic**: Funciona con cualquier modelo de embeddings, no esta atada a uno en especifico.
5. **Rapida para el volumen actual**: Con 21 documentos, ChromaDB responde en milisegundos.

Si el proyecto creciera a miles de documentos, se migraria a Qdrant (mejor escalabilidad) o pgvector (si ya hubiera PostgreSQL).

### Por que Docker

Ollama corre dentro de Docker por:

1. **Aislamiento**: Los modelos descargados estan dentro del volumen Docker, no ensucian el sistema de archivos del host.
2. **Reproducibilidad**: El `docker-compose.yml` define exactamente como debe correr Ollama. En cualquier otra maquina solo hace falta `docker compose up -d`.
3. **Facilidad de actualizacion**: Para actualizar Ollama solo se cambia la imagen: `docker compose pull && docker compose up -d`.
4. **Puerto mapeado**: Se mapea el puerto 11435 del host al 11434 del contenedor, evitando conflictos con una posible instalacion nativa de Ollama en el futuro.

Sin Docker, habria que instalar Ollama manualmente, configurarlo como servicio systemd, y gestionar actualizaciones a mano.

### Por que pypdf y BeautifulSoup

- **pypdf**: Libreria mas ligera para extraer texto de PDFs en este proyecto. Alternativas como `pdfplumber` o `PyMuPDF` son mas potentes pero pesan mas y no se justifican para el volumen actual de documentos.
- **BeautifulSoup**: Estandar de facto para parsear HTML en Python. Es confiable, bien documentada, y suficiente para extraer texto de archivos HTML.

### Por que RAGAS para metricas

RAGAS (RAG Assessment) es un marco de evaluacion especificamente disenado para sistemas RAG. Sus 4 metricas (Context Precision, Context Recall, Faithfulness, Answer Relevancy) miden exactamente lo que importa en este sistema: si recupera bien, si la informacion es suficiente, si el modelo alucina, y si responde lo que se le pregunto. No hay otro marco tan especifico para RAG.

---

## Glosario Rapido

| Termino | Que significa |
|---|---|
| **LLM** | Large Language Model - Modelo de lenguaje grande (IA que entiende texto) |
| **RAG** | Retrieval-Augmented Generation - Buscar + Generar |
| **Embedding** | Vector numerico que representa el significado de un texto |
| **Chunk** | Fragmento de texto de un documento |
| **Chunk size** | Tamanio maximo de cada fragmento en caracteres |
| **Overlap** | Solapamiento de texto entre fragmentos consecutivos |
| **Top-K** | Numero de fragmentos mas relevantes a recuperar |
| **Re-ranking** | Reordenar fragmentos usando el LLM para mayor precision |
| **Similitud del coseno** | Metrica que mide que tan similares son dos vectores (0 a 1) |
| **Alucinacion** | Cuando la IA inventa informacion que no esta en los datos |
| **HNSW** | Algoritmo de busqueda rapida en espacios vectoriales |
| **RAGAS** | RAG Assessment - Marco de metricas para evaluar RAG |
| **Endpoint** | URL de la API (ej: /api/generate, /api/embeddings) |
| **Token** | Unidad de texto que el modelo procesa (~0.75 palabras en promedio) |
| **Prompt** | Instruccion que se le da al LLM para que responda |
| **System Prompt** | Instruccion de comportamiento que se fija al inicio de la conversacion |
