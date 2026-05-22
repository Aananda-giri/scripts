from __future__ import annotations

import time
from collections.abc import Generator

from app.config import Settings
from app.core.embeddings import _detect_device
from app.core.embeddings import Embedder
from app.core.vector_store import QdrantStore
from app.core.retriever import HybridRetriever
from app.core.reranker import CrossEncoderReranker
from app.core.llm import LLM
from app.core.entity_extraction import EntityExtractor


class QueryPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings

        device = _detect_device(settings.device)
        self.embedder = Embedder(
            model_name=settings.embedding_model,
            device=device,
            cache_size=settings.embedding_cache_size,
        )
        self.vector_store = QdrantStore(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            collection_name=settings.collection_name,
        )
        self.retriever = HybridRetriever(self.vector_store, self.embedder)
        self.reranker = CrossEncoderReranker(device=device)
        self.llm = LLM(
            api_key=settings.openai_compatible_api_key,
            base_url=settings.openai_compatible_base_url,
            model=settings.llm_model,
        )
        self.entity_extractor = None
        if settings.entity_extraction_enabled:
            self.entity_extractor = EntityExtractor(
                api_key=settings.openai_compatible_api_key,
                base_url=settings.openai_compatible_base_url,
                model=settings.llm_model,
            )

    def _resolve_query(self, query: str, filters: dict | None):
        extracted_filters = {}
        search_query = query

        if filters is None and self.entity_extractor is not None:
            extraction = self.entity_extractor.extract(query)
            extracted_filters = extraction["filters"]
            search_query = extraction["semantic_query"]

        effective_filters = filters if filters is not None else (extracted_filters or None)
        return search_query, effective_filters, extracted_filters

    def _retrieve_and_rerank(self, query: str, search_query: str,
                              filters: dict | None, top_k: int):
        """Run retrieval + reranking. Returns (fused_results, top_results, timings)."""
        t0 = time.time()

        fused_results = self.retriever.retrieve(
            search_query,
            top_k=self.settings.hybrid_top_k,
            filters=filters,
            rrf_k=self.settings.rrf_constant_k,
            vector_top_k=self.settings.vector_search_top_k,
            bm25_top_k=self.settings.bm25_search_top_k,
            hybrid_top_k=self.settings.hybrid_top_k,
        )

        reranked = self.reranker.rerank(
            query, fused_results, top_n=self.settings.reranker_top_n
        )
        t2 = time.time()

        return fused_results, reranked[:top_k], {
            "fused_count": len(fused_results),
            "reranked_count": len(reranked),
            "retrieval_time_ms": round((t2 - t0) * 1000),
        }

    def _format_results(self, top_results: list[dict], top_k: int) -> list[dict]:
        return [
            {
                "job_id": r.get("job_id", ""),
                "job_title": r.get("job_title", ""),
                "company": r.get("company_name", ""),
                "location": r.get("job_location", ""),
                "job_level": r.get("job_level", ""),
                "job_category": r.get("job_category", ""),
                "relevance_score": round(r.get("rerank_score", 0.0), 4),
                "section_type": r.get("section_type", ""),
                "source_text": r.get("text", "") if top_k <= 10 else "",
            }
            for r in top_results
        ]

    def run_query(self, query: str, top_k: int = 5,
                  filters: dict | None = None,
                  skip_generation: bool = False) -> dict:
        t0 = time.time()

        search_query, effective_filters, extracted_filters = self._resolve_query(
            query, filters
        )

        fused_results, top_results, retrieval_meta = self._retrieve_and_rerank(
            query, search_query, effective_filters, top_k
        )
        t2 = time.time()

        if skip_generation:
            answer = ""
            t3 = t2
        else:
            answer = self.llm.generate_answer(search_query, top_results)
            t3 = time.time()

        return {
            "query": query,
            "search_query": search_query,
            "extracted_filters": extracted_filters,
            "answer": answer,
            "results": self._format_results(top_results, top_k),
            "processing_time_ms": round((t3 - t0) * 1000),
            "retrieval_details": {
                **retrieval_meta,
                "generation_time_ms": round((t3 - t2) * 1000),
            },
        }

    def run_query_stream(self, query: str, top_k: int = 5,
                         filters: dict | None = None) -> Generator[str, None, None]:
        """Yields LLM answer tokens. Use for SSE streaming."""
        search_query, effective_filters, extracted_filters = self._resolve_query(
            query, filters
        )

        _fused_results, top_results, _retrieval_meta = self._retrieve_and_rerank(
            query, search_query, effective_filters, top_k
        )

        yield from self.llm.generate_answer_stream(search_query, top_results)
