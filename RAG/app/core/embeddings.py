from __future__ import annotations

import functools
import threading
from collections import OrderedDict

from sentence_transformers import SentenceTransformer


def _detect_device(device: str = "auto") -> str:
    if device != "auto":
        return device
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


class _LRUEmbeddingCache:
    """Thread-safe LRU cache for query embeddings."""

    def __init__(self, max_size: int = 128):
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._lock = threading.Lock()
        self._max_size = max_size

    def get(self, key: str) -> list[float] | None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None

    def put(self, key: str, embedding: list[float]) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = embedding

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


class Embedder:
    def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1.5",
                 device: str = "auto", cache_size: int = 128):
        resolved = _detect_device(device)
        self.model = SentenceTransformer(
            model_name,
            trust_remote_code=True,
            device=resolved,
        )
        self._device = resolved
        self._cache = _LRUEmbeddingCache(max_size=cache_size)

    @property
    def device(self) -> str:
        return self._device

    def embed(self, text: str) -> list[float]:
        return (
            self.model.encode(
                f"search_document: {text}",
                normalize_embeddings=True,
            )
            .tolist()
        )

    def embed_query(self, query: str) -> list[float]:
        key = f"search_query: {query}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        embedding = (
            self.model.encode(
                key,
                normalize_embeddings=True,
            )
            .tolist()
        )
        self._cache.put(key, embedding)
        return embedding

    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 50,
        retry_max: int = 3,
        retry_delay: float = 2.0,
    ) -> list[list[float]]:
        prefixed = [f"search_document: {t}" for t in texts]
        return (
            self.model.encode(
                prefixed,
                batch_size=batch_size,
                show_progress_bar=True,
                normalize_embeddings=True,
            )
            .tolist()
        )
