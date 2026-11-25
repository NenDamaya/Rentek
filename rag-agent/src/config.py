import os

class Config:
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")
    # Modelo principal del chat: qwen3:8b con plantilla que respeta think=false.
    # rag-agent:4b queda para generación estructurada (JSON) por su plantilla.
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "rag-agent:8b")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")

    # === Presupuesto de contexto (RTX 4050 Laptop - 6 GB VRAM) ===
    # num_ctx incluye prompt + respuesta. En 6 GB no conviene subirlo de 8192
    # sin cuantizar el KV cache (OLLAMA_KV_CACHE_TYPE=q8_0).
    NUM_CTX = int(os.getenv("NUM_CTX", "8192"))
    NUM_PREDICT = int(os.getenv("NUM_PREDICT", "768"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
    KEEP_ALIVE = os.getenv("KEEP_ALIVE", "30m")
    # qwen3 razona antes de responder. Para el chat de atención conviene
    # desactivarlo: gasta tokens y puede agotar num_predict sin dar respuesta.
    OLLAMA_THINK = os.getenv("OLLAMA_THINK", "false").lower() == "true"

    # Compactación de historial: se dispara cuando el prompt supera este
    # presupuesto real (tokens estimados) y conserva los últimos turnos.
    COMPACT_THRESHOLD_TOKENS = int(os.getenv("COMPACT_THRESHOLD_TOKENS", "3000"))
    COMPACT_KEEP_RECENT = int(os.getenv("COMPACT_KEEP_RECENT", "4"))

    # Los resultados de herramientas se truncan antes de volver al modelo.
    TOOL_RESULT_MAX_CHARS = int(os.getenv("TOOL_RESULT_MAX_CHARS", "1800"))
    MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "4"))

    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "700"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "88"))

    TOP_K = int(os.getenv("TOP_K", "4"))

    SIMILARITY_METRIC = os.getenv("SIMILARITY_METRIC", "cosine")

    SIMILARITY_METRICS = ["cosine", "euclidean", "dot"]

    RERANK_ENABLED = os.getenv("RERANK_ENABLED", "false").lower() == "true"
    RERANK_TOP_N = int(os.getenv("RERANK_TOP_N", "5"))

    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "rentek_catalog_bge_m3")

    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "maquinaria_rag")
    DB_USER = os.getenv("DB_USER", "rag_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "rag_pass_2026")

    # Security & Cors Config
    AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "rentek-secret-key-change-in-production-2026")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")
    HTTPS_ONLY = os.getenv("HTTPS_ONLY", "false").lower() == "true"

config = Config()
