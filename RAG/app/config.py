from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # OpenAI-compatible API settings (DeepSeek by default for LLM)
    openai_compatible_api_key: str
    openai_compatible_base_url: str = "https://api.deepseek.com"  # DeepSeek
    embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"
    llm_model: str = "deepseek-chat"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_http_port: int = 6333
    collection_name: str = "job_chunks"

    chunk_max_size: int = 4000
    chunk_overlap: int = 200
    chunk_min_size: int = 100

    entity_extraction_enabled: bool = True

    device: str = "auto"

    embedding_cache_size: int = 128

    vector_search_top_k: int = 20
    bm25_search_top_k: int = 20
    hybrid_top_k: int = 10
    reranker_top_n: int = 5
    rrf_constant_k: int = 60

    embedding_dim: int = 768
    embedding_batch_size: int = 8
    embedding_retry_max: int = 3
    embedding_retry_delay: float = 2.0
