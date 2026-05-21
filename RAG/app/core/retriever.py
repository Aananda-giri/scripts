import re

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from rank_bm25 import BM25Okapi

from app.core.embeddings import Embedder
from app.core.vector_store import QdrantStore


class HybridRetriever:
    def __init__(self, vector_store: QdrantStore, embedder: Embedder):
        self.vector_store = vector_store
        self.embedder = embedder
        self.bm25: BM25Okapi | None = None
        self.bm25_chunks: list[dict] = []
        self._stemmer = PorterStemmer()
        try:
            self._stopwords = set(stopwords.words("english"))
        except LookupError:
            nltk.download("stopwords", quiet=True)
            self._stopwords = set(stopwords.words("english"))

    def build_bm25_index(self, chunks: list[dict]) -> None:
        self.bm25_chunks = chunks
        tokenized = [self._tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(tokenized)

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return [self._stemmer.stem(t) for t in tokens if t not in self._stopwords]

    def retrieve(self, query: str, top_k: int = 5,
                 filters: dict | None = None,
                 rrf_k: int = 60,
                 vector_top_k: int = 20,
                 bm25_top_k: int = 20,
                 hybrid_top_k: int = 10) -> list[dict]:

        vector_hits = self._vector_search(query, vector_top_k, filters)
        bm25_hits = self._bm25_search(query, bm25_top_k)

        fused = self._rrf_fuse(vector_hits, bm25_hits, k=rrf_k)

        result_ids = {hit["chunk_id"] for hit in fused[:hybrid_top_k] if hit["chunk_id"]}
        results = []
        for chunk in self.bm25_chunks:
            if chunk["chunk_id"] in result_ids:
                results.append(dict(chunk))
        return results[:top_k]

    def _vector_search(self, query: str, top_k: int,
                       filters: dict | None) -> list[dict]:
        query_vec = self.embedder.embed_query(query)
        hits = self.vector_store.search(query_vec, top_k=top_k,
                                        filter_cond=filters)
        return [
            {"chunk_id": h.payload.get("chunk_id", ""), "score": h.score,
             "chunk": dict(h.payload)}
            for h in hits
        ]

    def _bm25_search(self, query: str, top_k: int) -> list[dict]:
        if self.bm25 is None:
            return []
        tokens = self._tokenize(query)
        scores = self.bm25.get_scores(tokens)
        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [
            {"chunk_id": self.bm25_chunks[i]["chunk_id"], "score": float(score),
             "chunk": self.bm25_chunks[i]}
            for i, score in indexed[:top_k] if score > 0
        ]

    @staticmethod
    def _rrf_fuse(vector_hits: list[dict], bm25_hits: list[dict],
                  k: int = 60) -> list[dict]:
        scores: dict[str, float] = {}
        hits_map: dict[str, dict] = {}

        for rank, hit in enumerate(vector_hits, start=1):
            cid = hit["chunk_id"]
            scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank)
            if cid not in hits_map:
                hits_map[cid] = hit

        for rank, hit in enumerate(bm25_hits, start=1):
            cid = hit["chunk_id"]
            scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank)
            if cid not in hits_map:
                hits_map[cid] = hit

        sorted_ids = sorted(scores, key=scores.get, reverse=True)
        return [
            {**hits_map[cid], "rrf_score": scores[cid]}
            for cid in sorted_ids
        ]
