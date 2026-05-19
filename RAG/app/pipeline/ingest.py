from app.config import Settings
from app.core.preprocessing import load_and_chunk
from app.core.embeddings import GeminiEmbedder
from app.core.vector_store import QdrantStore


def run_ingestion(csv_path: str, settings: Settings) -> int:
    print(f"Loading and chunking: {csv_path}")
    chunks = load_and_chunk(
        csv_path,
        max_size=settings.chunk_max_size,
        overlap=settings.chunk_overlap,
        min_size=settings.chunk_min_size,
    )
    print(f"Total chunks: {len(chunks)}")

    embedder = GeminiEmbedder(
        api_key=settings.gemini_api_key,
        model=settings.embedding_model,
    )
    print(f"Generating embeddings (batch_size={settings.embedding_batch_size})...")
    texts = [c["text"] for c in chunks]
    vectors = embedder.embed_batch(
        texts,
        batch_size=settings.embedding_batch_size,
        retry_max=settings.embedding_retry_max,
        retry_delay=settings.embedding_retry_delay,
    )
    print(f"Generated {len(vectors)} embeddings")

    store = QdrantStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.collection_name,
    )
    store.create_collection(vector_size=768, recreate=True)
    count = store.upsert_chunks(chunks, vectors)
    print(f"Upserted {count} points to Qdrant collection '{settings.collection_name}'")

    info = store.collection_info()
    print(f"Collection info: {info}")
    return count
