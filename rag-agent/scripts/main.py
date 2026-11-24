#!/usr/bin/env python3
import argparse
import sys
from src.rag import RAGSystem
from config import config


def main():
    parser = argparse.ArgumentParser(description="Sistema RAG con Ollama")
    parser.add_argument("--metric", choices=config.SIMILARITY_METRICS, default=config.SIMILARITY_METRIC,
                        help="Métrica de similitud (cosine, euclidean, dot)")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Ingestar un documento")
    ingest.add_argument("file", help="Ruta al archivo (PDF, HTML, TXT)")
    ingest.add_argument("--metadata", nargs="*", help="Metadatos en formato key=value")

    query = subparsers.add_parser("query", help="Hacer una pregunta")
    query.add_argument("question", help="Pregunta a responder")
    query.add_argument("--top-k", type=int, default=config.TOP_K, help="Número de fragmentos a recuperar")
    query.add_argument("--no-rerank", action="store_true", help="Desactivar re-ranking")
    query.add_argument("--verbose", action="store_true", help="Mostrar fuentes recuperadas")

    stats = subparsers.add_parser("stats", help="Ver estadísticas de la base")

    quality = subparsers.add_parser("quality", help="Evaluar calidad de recuperación de una pregunta")
    quality.add_argument("question", help="Pregunta a evaluar")

    delete = subparsers.add_parser("delete", help="Eliminar fragmentos por metadata")
    delete.add_argument("--where", nargs="*", required=True, help="Filtro en formato key=value (ej: categoria=tarea)")

    chat = subparsers.add_parser("chat", help="Modo conversacional interactivo")
    chat.add_argument("--top-k", type=int, default=config.TOP_K, help="Numero de fragmentos a recuperar")
    chat.add_argument("--no-rerank", action="store_true", help="Desactivar re-ranking")
    chat.add_argument("--verbose", action="store_true", help="Mostrar fuentes recuperadas")

    args = parser.parse_args()
    
    rag = RAGSystem()
    
    if getattr(args, 'no_rerank', False):
        config.RERANK_ENABLED = False
    if args.metric != config.SIMILARITY_METRIC:
        print(f"Nota: Cambiando métrica a {args.metric}. Esto requiere recrear la colección para efectos completos.")

    if args.command == "ingest":
        metadata = {}
        if args.metadata:
            for item in args.metadata:
                if "=" in item:
                    k, v = item.split("=", 1)
                    metadata[k] = v
        
        num_chunks = rag.ingest_document(args.file, metadata)
        print(f"[OK] Documento ingestado: {num_chunks} fragmentos creados")

    elif args.command == "query":
        result = rag.query(
            args.question, 
            args.top_k,
        )
        
        print("\n" + "="*60)
        print("RESPUESTA")
        print("="*60)
        print(result["answer"])
        
        search_ms = result.get('latency_search_ms', 0)
        gen_ms = result.get('latency_generation_ms', 0)
        print(f"\nTiempo Total: {result['latency_ms']:.0f} ms  |  Busqueda: {search_ms:.0f} ms  |  Generacion: {gen_ms:.0f} ms")
        
        if getattr(args, 'verbose', False):
            print("\n" + "="*60)
            print(f"FUENTES RECUPERADAS (Top-{len(result['sources'])})")
            print("="*60)
            for i, source in enumerate(result["sources"], 1):
                score_info = f" [score: {result['rerank_scores'][i-1]:.3f}]" if result.get("rerank_scores") else ""
                print(f"\n[{i}]{score_info}")
                print(f"  {source[:300]}...")

    elif args.command == "stats":
        stats = rag.get_stats()
        print("="*60)
        print("ESTADÍSTICAS DEL SISTEMA RAG")
        print("="*60)
        print(f"  Fragmentos almacenados: {stats['total_documents']}")
        print(f"  Métrica de similitud:   {stats['similarity_metric']}")
        print(f"  Re-ranking activado:     {stats['rerank_enabled']}")
        print(f"  Chunk size:              {stats['chunk_size']}")
        print(f"  Chunk overlap:          {stats['chunk_overlap']}")
        print(f"  Top-K:                  {stats['top_k']}")
        if "avg_latency_ms" in stats:
            print(f"\n  Latencia total promedio: {stats['avg_latency_ms']:.0f} ms")
            print(f"  Latencia búsqueda p95:   {stats['p95_search_ms']:.0f} ms")
            print(f"  Total de consultas:      {stats['total_queries']}")

    elif args.command == "quality":
        quality = rag.get_retrieval_quality(args.question)
        print("="*60)
        print("EVALUACIÓN DE RECUPERACIÓN")
        print("="*60)
        print(f"  Documentos recuperados:  {quality['retrieved_docs']}")
        print(f"  Score promedio:         {quality['avg_score']:.4f}")
        
        print("\nTop 3 documentos:")
        for i, doc in enumerate(quality["top_documents"], 1):
            print(f"  [{i}] score: {doc['score']:.4f} - {doc['document'][:100]}...")

    elif args.command == "chat":
        print("Modo conversacional. Escribe 'salir' para terminar.\n")
        history = ""
        while True:
            try:
                pregunta = input("Tu pregunta: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            
            if not pregunta:
                continue
            if pregunta.lower() in ("salir", "exit", "quit", "q"):
                break
            
            result = rag.query(pregunta, args.top_k, conversation_history=history)
            
            print("\n" + "="*60)
            print("RESPUESTA")
            print("="*60)
            print(result["answer"])
            
            search_ms = result.get('latency_search_ms', 0)
            gen_ms = result.get('latency_generation_ms', 0)
            print(f"\nTiempo Total: {result['latency_ms']:.0f} ms  |  Busqueda: {search_ms:.0f} ms  |  Generacion: {gen_ms:.0f} ms")
            
            if getattr(args, 'verbose', False):
                print("\n" + "="*60)
                print(f"FUENTES RECUPERADAS (Top-{len(result['sources'])})")
                print("="*60)
                for i, source in enumerate(result["sources"], 1):
                    score_info = f" [score: {result['rerank_scores'][i-1]:.3f}]" if result.get("rerank_scores") else ""
                    print(f"\n[{i}]{score_info}")
                    print(f"  {source[:300]}...")
            
            history += f"Usuario: {pregunta}\nAsistente: {result['answer']}\n"
            
            print("\n" + "-"*60)
            respuesta = input("¿Quieres preguntar algo mas? (s/n): ").strip().lower()
            if respuesta not in ("s", "si", "sí", "yes", "y"):
                print("¡Hasta luego!")
                break
            print()
    
    elif args.command == "delete":
        metadata_filter = {}
        for item in args.where:
            if "=" in item:
                k, v = item.split("=", 1)
                metadata_filter[k] = v
        rag.vector_store.delete_by_metadata(metadata_filter)
        total = rag.vector_store.count()
        print(f"[OK] Fragmentos eliminados (filtro: {metadata_filter})")
        print(f"  Restantes en la BD: {total}")


if __name__ == "__main__":
    main()