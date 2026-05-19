from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    gemini_api_key: str
    embedding_model: str = "text-embedding-004"
    llm_model: str = "gemini-2.0-flash"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_http_port: int = 6333
    collection_name: str = "job_chunks"

    chunk_max_size: int = 1000
    chunk_overlap: int = 200
    chunk_min_size: int = 100

    vector_search_top_k: int = 20
    bm25_search_top_k: int = 20
    hybrid_top_k: int = 10
    reranker_top_n: int = 5
    rrf_constant_k: int = 60

    embedding_batch_size: int = 50
    embedding_retry_max: int = 3
    embedding_retry_delay: float = 2.0
