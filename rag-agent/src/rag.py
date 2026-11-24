import json
import os
import uuid
import time
from pathlib import Path
from typing import List, Optional, Dict
import numpy as np

from src.document_loader import DocumentLoader
from src.text_chunker import TextChunker
from src.vector_store import VectorStore
from src.ollama_client import OllamaClient
from src.reranker import ReRanker
from .config import config


LATENCY_FILE = ".rag_latencies.json"


def _load_latencies():
    try:
        with open(LATENCY_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_latencies(data):
    with open(LATENCY_FILE, "w") as f:
        json.dump(data, f)


class RAGSystem:
    def __init__(self):
        self.vector_store = VectorStore()
        self.ollama = OllamaClient()
        self.chunker = TextChunker(config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        self.reranker = ReRanker()
        self.query_times = _load_latencies()

    def ingest_document(self, file_path: str, metadata: Optional[dict] = None) -> int:
        text = DocumentLoader.load(file_path)
        chunks = self.chunker.chunk(text)
        
        embeddings = self.ollama.get_embeddings(chunks)
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [metadata or {} for _ in chunks]
        
        self.vector_store.add_documents(ids, embeddings, chunks, metadatas)
        
        return len(chunks)

    def query(self, question: str, top_k: int = None, enable_rerank: bool = None, conversation_history: str = "") -> dict:
        t0 = time.time()
        
        top_k = top_k or config.TOP_K
        enable_rerank = enable_rerank if enable_rerank is not None else config.RERANK_ENABLED
        
        query_embedding = self.ollama.get_embeddings([question])[0]
        t1 = time.time()
        
        total_docs = self.vector_store.count()
        search_k = max(top_k * 2, total_docs) if total_docs > top_k else top_k
        results = self.vector_store.search(query_embedding, search_k)
        t2 = time.time()
        
        contexts = results["documents"][0]
        
        all_scores = None
        if enable_rerank and len(contexts) > 1:
            reranked = self.reranker.rerank(question, contexts, min(config.RERANK_TOP_N, len(contexts)))
            final_contexts = [r["document"] for r in reranked]
            all_scores = [r["score"] for r in reranked]
        else:
            final_contexts = contexts[:top_k]
            all_scores = None
        t3 = time.time()
        
        docs_str = "\n\n".join(final_contexts)
        context_str = docs_str
        if conversation_history:
            context_str = f"{conversation_history}\n\nInformacion recuperada:\n{docs_str}"
        
        answer = self.ollama.generate(question, context_str)
        t4 = time.time()
        
        latency_total = (t4 - t0) * 1000
        latency_embedding = (t1 - t0) * 1000
        latency_search = (t2 - t1) * 1000
        latency_rerank = (t3 - t2) * 1000
        latency_generation = (t4 - t3) * 1000
        self.query_times.append({"total_ms": latency_total, "search_ms": latency_search})
        _save_latencies(self.query_times[-100:])
        
        return {
            "answer": answer,
            "context": context_str,
            "sources": final_contexts,
            "rerank_scores": all_scores,
            "latency_ms": latency_total,
            "latency_search_ms": latency_search,
            "latency_generation_ms": latency_generation,
        }

    def get_stats(self) -> dict:
        stats = {
            "total_documents": self.vector_store.count(),
            "similarity_metric": config.SIMILARITY_METRIC,
            "rerank_enabled": config.RERANK_ENABLED,
            "chunk_size": config.CHUNK_SIZE,
            "chunk_overlap": config.CHUNK_OVERLAP,
            "top_k": config.TOP_K
        }
        
        if self.query_times:
            totals = [t["total_ms"] for t in self.query_times]
            searches = [t["search_ms"] for t in self.query_times]
            stats["avg_latency_ms"] = round(np.mean(totals), 2)
            stats["p95_latency_ms"] = round(np.percentile(totals, 95), 2)
            stats["p95_search_ms"] = round(np.percentile(searches, 95), 2)
            stats["total_queries"] = len(self.query_times)
        
        return stats

    def get_retrieval_quality(self, question: str) -> Dict:
        query_embedding = self.ollama.get_embeddings([question])[0]
        total_docs = self.vector_store.count()
        search_k = max(total_docs, config.TOP_K)
        results = self.vector_store.search_with_scores(query_embedding, search_k)
        
        return {
            "retrieved_docs": len(results),
            "avg_score": round(np.mean([r["score"] for r in results]), 4) if results else 0,
            "top_documents": results[:3]
        }