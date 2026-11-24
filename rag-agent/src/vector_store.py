import chromadb
from chromadb.config import Settings
from typing import List, Optional
import numpy as np

from .config import config


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        metric_map = {
            "cosine": "cosine",
            "euclidean": "l2",
            "dot": "ip"
        }
        
        index_params = {
            "hnsw:space": metric_map.get(config.SIMILARITY_METRIC, "cosine"),
            "hnsw:M": 32,
            "hnsw:construction_ef": 200,
        }
        
        self.collection = self.client.get_or_create_collection(
            name=config.COLLECTION_NAME,
            metadata=index_params
        )

    def add_documents(self, ids: List[str], embeddings: List[np.ndarray], documents: List[str], metadatas: Optional[List[dict]] = None):
        if metadatas is None or all(not m for m in metadatas):
            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings,
                documents=documents,
            )
        else:
            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist() if isinstance(embeddings, np.ndarray) else embeddings,
                documents=documents,
                metadatas=metadatas,
            )

    def search(self, query_embedding: np.ndarray, top_k: int = None) -> dict:
        top_k = top_k or config.TOP_K
        
        if config.SIMILARITY_METRIC == "euclidean":
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding],
                n_results=top_k
            )
            if "distances" in results and results["distances"]:
                results["distances"] = [[1 / (1 + d) for d in results["distances"][0]]]
        else:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist() if isinstance(query_embedding, np.ndarray) else query_embedding],
                n_results=top_k
            )
        
        return results

    def search_with_scores(self, query_embedding: np.ndarray, top_k: int = None) -> List[dict]:
        top_k = top_k or config.TOP_K
        results = self.search(query_embedding, top_k)
        
        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        return [
            {"document": doc, "score": score, "metadata": meta}
            for doc, score, meta in zip(docs, distances, metadatas)
        ]

    def delete_collection(self):
        self.client.delete_collection(config.COLLECTION_NAME)

    def delete_by_metadata(self, metadata_filter: dict):
        self.collection.delete(where=metadata_filter)

    def count(self) -> int:
        return self.collection.count()

    def get_all_documents(self) -> List[dict]:
        return self.collection.get()["documents"]