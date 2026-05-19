import time

from app.config import Settings
from app.core.embeddings import GeminiEmbedder
from app.core.vector_store import QdrantStore
from app.core.retriever import HybridRetriever
from app.core.reranker import CrossEncoderReranker
from app.core.llm import GeminiLLM


class QueryPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedder = GeminiEmbedder(
            api_key=settings.gemini_api_key,
            model=settings.embedding_model,
        )
        self.vector_store = QdrantStore(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            collection_name=settings.collection_name,
        )
        self.retriever = HybridRetriever(self.vector_store, self.embedder)
        self.reranker = CrossEncoderReranker()
        self.llm = GeminiLLM(
            api_key=settings.gemini_api_key,
            model=settings.llm_model,
        )

    def run_query(self, query: str, top_k: int = 5,
                  filters: dict | None = None) -> dict:
        t0 = time.time()

        fused_results = self.retriever.retrieve(
            query,
            top_k=self.settings.hybrid_top_k,
            filters=filters,
            rrf_k=self.settings.rrf_constant_k,
            vector_top_k=self.settings.vector_search_top_k,
            bm25_top_k=self.settings.bm25_search_top_k,
            hybrid_top_k=self.settings.hybrid_top_k,
        )
        t1 = time.time()

        reranked = self.reranker.rerank(
            query, fused_results, top_n=self.settings.reranker_top_n
        )
        t2 = time.time()

        top_results = reranked[:top_k]
        answer = self.llm.generate_answer(query, top_results)
        t3 = time.time()

        return {
            "query": query,
            "answer": answer,
            "results": [
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
            ],
            "processing_time_ms": round((t3 - t0) * 1000),
            "retrieval_details": {
                "fused_count": len(fused_results),
                "reranked_count": len(reranked),
                "retrieval_time_ms": round((t2 - t0) * 1000),
                "generation_time_ms": round((t3 - t2) * 1000),
            },
        }
