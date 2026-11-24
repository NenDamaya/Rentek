import re
import requests
from typing import List, Dict
from .config import config


class ReRanker:
    def __init__(self, ollama_client=None):
        self.ollama = ollama_client

    def _parse_score(self, text: str) -> float:
        text = text.strip()
        try:
            return max(0.0, min(1.0, float(text)))
        except ValueError:
            pass
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            try:
                return max(0.0, min(1.0, float(match.group(1))))
            except ValueError:
                pass
        return 0.5

    def rerank(self, query: str, documents: List[str], top_n: int = None) -> List[Dict]:
        top_n = top_n or config.RERANK_TOP_N
        
        scored_docs = []
        for i, doc in enumerate(documents):
            preview = doc[:800]
            prompt = f"""Evalúa la relevancia del documento para responder la pregunta.
Puntuación de 0 a 1, donde 1 es muy relevante.

Pregunta: {query}

Documento: {preview}

Puntuación:"""
            
            try:
                response = requests.post(
                    f"{config.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": config.OLLAMA_MODEL,
                        "prompt": prompt,
                        "system": "Responde únicamente con un número entre 0 y 1, nada más.",
                        "stream": False,
                        "keep_alive": "10m",
                        "options": {
                            "num_gpu": 999,
                            "main_gpu": 0,
                        }
                    }
                )
                score = self._parse_score(response.json()["response"].strip())
            except:
                score = 0.5
            
            scored_docs.append({"index": i, "document": doc, "score": score})
        
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_docs[:top_n]


class ReciprocalRankFusion:
    @staticmethod
    def fuse(results_list: List[List[Dict]], k: int = 60) -> List[Dict]:
        scores = {}
        
        for results in results_list:
            for rank, doc in enumerate(results, 1):
                doc_id = doc["index"]
                if doc_id not in scores:
                    scores[doc_id] = {"document": doc["document"], "score": 0.0}
                scores[doc_id]["score"] += 1 / (k + rank)
        
        fused = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        return fused