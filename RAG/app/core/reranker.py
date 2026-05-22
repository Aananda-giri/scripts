from __future__ import annotations

from sentence_transformers import CrossEncoder

from app.core.embeddings import _detect_device


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
                 device: str = "auto"):
        resolved = _detect_device(device)
        self.model = CrossEncoder(model_name, max_length=512, device=resolved)
        self._device = resolved

    @property
    def device(self) -> str:
        return self._device

    def rerank(self, query: str, candidates: list[dict],
               top_n: int = 5) -> list[dict]:
        if not candidates:
            return []

        pairs = [(query, c["text"][:512]) for c in candidates]
        scores = self.model.predict(pairs)

        scored = []
        for candidate, score in zip(candidates, scores):
            c = dict(candidate)
            c["rerank_score"] = float(score)
            scored.append(c)

        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored[:top_n]
