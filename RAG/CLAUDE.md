# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Start Qdrant (required for local dev)
docker compose up -d qdrant

# Install dependencies
pip install -r requirements.txt

# Configure (edit .env with OPENAI_COMPATIBLE_API_KEY after copying)
cp .env.example .env

# Ingest job listings into Qdrant
python scripts/ingest.py "LF Jobs - LF Jobs.csv"

# Run API server
uvicorn app.main:app --reload --port 8000

# Full Docker stack (Qdrant + API)
OPENAI_COMPATIBLE_API_KEY=your-key docker compose up --build
```

There are no tests, linters, or type checkers configured.

## Architecture

This is a multi-stage RAG pipeline over ~1,000 job listings: entity extraction → hybrid retrieval (vector + BM25 → RRF fusion) → dedup by job_id → cross-encoder rerank → LLM generation. It exposes a FastAPI server with a single-page search UI.

LLM uses DeepSeek via OpenAI-compatible API. Embeddings use `nomic-ai/nomic-embed-text-v1.5` loaded in-process via `sentence-transformers`.

### Retrieval pipeline (per query)

1. **Entity extraction** (when no manual filters provided): LLM extracts `job_category`, `job_level`, and `tags` from the natural language query, validated against known allowed values. Also produces a cleaned `semantic_query` for embedding. Manual filters from the UI skip this step.
2. **Dense**: `nomic-embed-text-v1.5` (768-dim) → Qdrant cosine search (top-20) with metadata filters from entity extraction or manual input
3. **Sparse**: In-memory BM25 keyword search (top-20) using `rank-bm25` + NLTK Porter stemming + stopword removal
4. **Fusion**: Reciprocal Rank Fusion (k=60) merges both rankings, then deduplicates by `job_id` (keeps highest-scoring chunk per job)
5. **Rerank**: `cross-encoder/ms-marco-MiniLM-L-6-v2` scores each candidate, returns top-5
6. **Generate**: `deepseek-chat` (temperature 0.3) with a system prompt that enforces source grounding, citations, and structured output

### Key modules

| Module | Path | Role |
|---|---|---|
| Config | `app/config.py` | Pydantic `BaseSettings` loaded from `.env` — all tunables live here (top-k values, batch sizes, model names, chunk params, entity extraction toggle) |
| Preprocessing | `app/core/preprocessing.py` | CSV → clean HTML → section-aware chunking (4000-char max). Builds enriched `embedding_text` with job metadata. Splits `tags` into array. |
| Embeddings | `app/core/embeddings.py` | `sentence-transformers` wrapper for `nomic-ai/nomic-embed-text-v1.5`. Uses `search_document`/`search_query` prefixes per nomic convention |
| Entity Extraction | `app/core/entity_extraction.py` | LLM-based extraction of `job_category`, `job_level`, `tags` from NL queries with validation against known allowed values |
| Vector Store | `app/core/vector_store.py` | Qdrant client: creates collection with INT8 quantization + HNSW + payload indexes (keyword: job_category, job_level, company_name, job_location, tags; datetime: publication_date), upserts in batches of 100, search with `MatchAny` filters |
| Retriever | `app/core/retriever.py` | `HybridRetriever` owns the BM25 index and orchestrates vector + BM25 + RRF. Deduplicates by `job_id` after fusion. BM25 is built at startup in `main.py` lifespan |
| Reranker | `app/core/reranker.py` | Thin wrapper around `sentence-transformers` CrossEncoder, truncates inputs to 512 chars |
| LLM | `app/core/llm.py` | DeepSeek prompt builder. Formats chunks as `[Source: LF#### - Title at Company]`, caps chunks at 800 chars each, 1024 output tokens |
| Query Pipeline | `app/pipeline/query.py` | Wires entity extraction → embedder → retriever → reranker → LLM, returns timed dict. Supports `skip_generation` for search-only mode |
| Ingestion Pipeline | `app/pipeline/ingest.py` | CSV → chunks → enriched embedding_text → embeddings → Qdrant upsert orchestrator |
| API | `app/api/router.py` + `schemas.py` | Three endpoints: `POST /api/query`, `POST /api/search` (no LLM), `GET /api/health`. Filter fields: `job_category`, `job_level`, `company_name`, `job_location` |
| App entry | `app/main.py` | Lifespan builds pipeline, runs BM25 indexing on startup if CSV is present |

### Data flow

**Ingestion**: CSV (1,000 rows) → `clean_html` (BeautifulSoup, `<br>`→`\n`) → `extract_metadata` (9 fields, missing locations imputed, tags split to array) → `chunk_description` (regex section detection → paragraph split → 4,000-char max, 200-char overlap) → `build_embedding_text` (enriched with job title, company, category, level, location) → sentence-transformers embed (batch of 50) → Qdrant upsert. Produces ~3,000–4,000 chunks.

**Query**: User query → entity extraction (LLM extracts filters + semantic_query) → `embed_query` → vector search with filters + BM25 → RRF fusion → dedup by job_id → cross-encoder → LLM generation → JSON response with answer + extracted filters + ranked results + timing metadata.

### Important design details

- **BM25 index is in-memory and lost on restart.** It's rebuilt during the FastAPI lifespan hook if the CSV file exists at the expected path. Vector data persists in Qdrant's Docker volume.
- **The CSV is hardcoded** in `main.py` as `"LF Jobs - LF Jobs.csv"` relative to the project root.
- **No authentication, rate limiting, or caching** — single-user design.
- **Chunk IDs use `abs(hash(chunk_id)) % 2**63`** for Qdrant point IDs — collision risk is negligible at this scale but worth noting.
- **Docker Compose** sets `QDRANT_HOST=qdrant` for the app container (Docker network DNS) vs the default `localhost` (local dev).
- **Cross-encoder model (~80MB) downloads on first import** from Hugging Face, as do NLTK stopwords/punkt data.
- **Entity extraction** uses DeepSeek with temperature 0.0 and validated against hardcoded allowed values. Manual filters from the UI bypass entity extraction entirely.
- **Embeddings use enriched text** (title + company + category + level + location + description), not just the raw chunk text. This gives dense search visibility into structured metadata.
- **Tags are stored as arrays** in Qdrant payload, enabling `MatchAny` filtering. Publication dates are indexed as datetime for potential range queries.
- **Deduplication by job_id** happens after RRF fusion (before reranking), keeping only the highest-scoring chunk per job.
