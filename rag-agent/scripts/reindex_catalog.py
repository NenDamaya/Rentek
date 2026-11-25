"""Reindexa el catálogo de maquinaria en la colección configurada.

Uso:
    python scripts/reindex_catalog.py
    RESET=1 python scripts/reindex_catalog.py   # borra la colección antes

Se ejecuta dentro del contenedor o en un entorno con las dependencias del
proyecto. Requiere Ollama disponible con el modelo de embeddings configurado.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import config
from src.rag import RAGSystem


def main() -> int:
    rag = RAGSystem()

    if os.getenv("RESET", "false").lower() in ("1", "true", "yes"):
        try:
            rag.vector_store.delete_collection()
            print("colección anterior eliminada")
        except Exception as exc:
            print(f"no se pudo eliminar la colección: {exc}")
        rag = RAGSystem()

    candidates = [
        os.getenv("REINDEX_FILE", ""),
        "data/documentos/Maquinarias.txt",
        "data/documentos/Maquinarias.md",
    ]
    file_path = next((p for p in candidates if p and Path(p).exists()), None)
    if not file_path:
        print("No se encontró el catálogo en data/documentos/", file=sys.stderr)
        return 1

    chunks = rag.ingest_document(file_path, {"source": Path(file_path).name, "tipo": "catalogo"})
    total = rag.vector_store.count()
    print(
        f"archivo={file_path} chunks={chunks} total={total} "
        f"collection={config.COLLECTION_NAME} embeddings={config.EMBEDDING_MODEL}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
