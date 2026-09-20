"""Hybrid RAG module combining BM25 keyword retrieval and ChromaDB vector search.

Provides high-precision grounding over project telemetry and status records.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List
from agents.retrieval.vector_store import LocalVectorStore


class BM25Retriever:
    """Simple BM25 keyword retriever implementation for hybrid ranking."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_len: List[int] = []
        self.avgdl: float = 0.0
        self.doc_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}
        self.documents: List[Dict[str, Any]] = []

    def fit(self, documents: List[Dict[str, Any]]) -> None:
        self.documents = documents
        total_len = 0
        df: Dict[str, int] = {}

        for doc in documents:
            tokens = doc["content"].lower().split()
            self.doc_len.append(len(tokens))
            total_len += len(tokens)
            freqs: Dict[str, int] = {}
            for t in tokens:
                freqs[t] = freqs.get(t, 0) + 1
            self.doc_freqs.append(freqs)
            for t in set(tokens):
                df[t] = df.get(t, 0) + 1

        num_docs = len(documents)
        self.avgdl = total_len / max(1, num_docs)

        for term, freq in df.items():
            self.idf[term] = math.log((num_docs - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_tokens = query.lower().split()
        scores = []

        for i, doc in enumerate(self.documents):
            score = 0.0
            doc_len = self.doc_len[i]
            freqs = self.doc_freqs[i]

            for term in query_tokens:
                if term not in freqs:
                    continue
                f = freqs[term]
                idf = self.idf.get(term, 0.0)
                denom = f + self.k1 * (1 - self.b + self.b * (doc_len / max(1, self.avgdl)))
                score += idf * (f * (self.k1 + 1)) / max(1e-6, denom)

            scores.append((score, doc))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [{"doc": doc, "bm25_score": s} for s, doc in scores[:top_k]]


class HybridRAGRetriever:
    """Hybrid RAG combining BM25 keyword matching and Vector similarity search."""

    def __init__(self, vector_store: LocalVectorStore):
        self.vector_store = vector_store
        self.bm25 = BM25Retriever()
        self._fitted = False

    def fit_if_needed(self) -> None:
        if not self._fitted:
            if not self.vector_store.documents:
                self.vector_store.build_index()
            docs = [
                {"id": doc.doc_id, "content": doc.content, "metadata": doc.metadata}
                for doc in self.vector_store.documents
            ]
            self.bm25.fit(docs)
            self._fitted = True

    def retrieve(self, query: str, top_k: int = 9) -> List[Dict[str, Any]]:
        """Retrieve documents combining vector search and BM25 scores."""
        self.fit_if_needed()

        vector_hits = self.vector_store.similarity_search(query, top_k=top_k)
        bm25_hits = self.bm25.search(query, top_k=top_k)

        # Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        for rank, hit in enumerate(vector_hits):
            doc_id = hit["id"]
            doc_map[doc_id] = hit
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60 + rank + 1))

        for rank, item in enumerate(bm25_hits):
            doc = item["doc"]
            doc_id = doc["id"]
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "id": doc_id,
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                }
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60 + rank + 1))

        hybrid_results = []
        for doc_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            item = doc_map[doc_id]
            item["rrf_score"] = round(rrf_score, 4)
            hybrid_results.append(item)

        return hybrid_results[:top_k]
