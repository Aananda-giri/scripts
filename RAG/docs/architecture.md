# Architecture

## Overview

The RAG pipeline retrieves relevant job listings for natural language queries and generates grounded answers via an OpenAI-compatible LLM (DeepSeek by default). It uses a three-stage retrieval strategy: dense vector search (semantic) + sparse keyword search (exact match) fused via Reciprocal Rank Fusion, then re-ranked by a cross-encoder for final precision.

## System Diagram

```
┌──────────┐     ┌─────────────────────────────────────────────┐
│  Client   │────▶│  FastAPI (uvicorn)                          │
└──────────┘     │  POST /api/query                            │
                  │  GET  /api/health                           │
                  └──────┬──────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
      ┌──────────┐ ┌──────────┐ ┌───────────┐
      │ Embedder │ │Retriever │ │  LLM      │
      │ (Ollama) │ │(Hybrid)  │ │(DeepSeek) │
      └────┬─────┘ └────┬─────┘ └───────────┘
           │            │
           ▼            ▼
      ┌────────────────────────┐
      │  Qdrant Vector Store   │
      │  (Cosine, HNSW, INT8)  │
      └────────────────────────┘
```

## Data Flow

### Ingestion

```
CSV (1000 rows)
  │
  ├─ load_jobs_csv()          csv.DictReader, UTF-8-SIG
  ├─ clean_html()             BeautifulSoup, <br>→\n, collapse whitespace
  ├─ extract_metadata()       9 standardized fields, impute missing locations
  ├─ chunk_description()      Section detection → split → 1000-char chunks
  │
  ├─ Embedder.embed_batch()         Batch of 50 via Ollama (nomic-embed-text)
  │
  └─ QdrantStore.upsert_chunks()    Points with payload + payload indexes
```

### Query

```
User query (natural language)
  │
  ├─ Embedder.embed_query()               Single text embedding
  │
  ├─ QdrantStore.search()                 Cosine top-20 + optional payload filter
  ├─ HybridRetriever._bm25_search()       BM25 tokenized top-20
  │
  ├─ HybridRetriever._rrf_fuse()          RRF(k=60) → top-10 unified ranking
  │
  ├─ CrossEncoderReranker.rerank()        MiniLM scores (query, chunk) → top-5
  │
  └─ LLM.generate_answer()                System prompt + context → response
```

## Engineering Decisions

### 1. Embedding Model: `nomic-embed-text-v1.5` (via Ollama)

Runs locally through Ollama's OpenAI-compatible API. 768-dimensional vectors.
No API costs or rate limits — embeddings are generated entirely on your machine.
Any OpenAI-compatible embedding API can be substituted via `EMBEDDING_MODEL`
and `OPENAI_COMPATIBLE_EMBEDDING_BASE_URL`.

**Alternatives considered:** Cohere Embed v3 (requires separate API key),
OpenAI text-embedding-3-small (1536-dim, paid API),
Hugging Face all-MiniLM-L6-v2 (384-dim, lower quality, runs locally).

### 2. LLM Model: `deepseek-chat`

DeepSeek's flagship chat model via their OpenAI-compatible API. Low temperature
(0.3) keeps responses factual and grounded. Any OpenAI-compatible model can be
substituted via `LLM_MODEL` and `OPENAI_COMPATIBLE_BASE_URL` env vars.

### 3. Vector Store: Qdrant

Chosen over Pinecone (external dependency), Chroma (less performant at scale),
and Weaviate (heavier). Qdrant runs locally in Docker, has excellent Rust
performance, supports payload indexes for filtered search, scalar quantization
for memory efficiency, and HNSW for fast approximate nearest neighbor search.

**Collection configuration:**

| Parameter | Value | Rationale |
|---|---|---|
| Distance | Cosine | Standard for normalized embeddings |
| HNSW m | 16 | Good balance for ~10k vectors |
| ef_construct | 100 | Quality during index build |
| Quantization | INT8 scalar | 4× memory reduction, negligible recall loss |
| Payload indexes | category, level, company, location | Fast filtered search |

### 4. Semantic Chunking

Job descriptions have clear internal structure (Responsibilities, Skills,
Qualifications, Benefits, etc.). Fixed-size window chunking would split
semantically related content across chunks, degrading retrieval quality.

Our approach:
1. Detect section headings with a curated regex pattern covering the common
   heading styles found across 145 companies' job postings
2. Split at heading boundaries first, preserving section-level coherence
3. Within sections exceeding 1000 chars, split by paragraph, then by sentence
4. Apply 200-char overlap between adjacent chunks to avoid boundary truncation
5. Each chunk carries full job metadata (title, company, category, level,
   location) as payload for filtering and context in the LLM prompt

**Result:** ~6,000–7,000 chunks from 1,000 jobs (6–7 chunks per job on average).
Each chunk is a self-contained, semantically coherent unit.

### 5. Hybrid Search: Vector + BM25 → RRF

Pure vector search excels at semantic similarity but struggles with exact term
matches (e.g., "Python" vs "software engineer with scripting experience").
BM25 excels at keyword precision but misses semantic equivalence. Combining
both captures the strengths of each.

**Reciprocal Rank Fusion** (k=60) was chosen over score normalization because:
- Vector (cosine) and BM25 scores have different scales and distributions
- RRF uses only rank position, which is directly comparable
- No weight tuning required — proven robust across datasets
- The constant k=60 dampens the advantage of being ranked #1 vs #2

### 6. Cross-Encoder Reranker: `ms-marco-MiniLM-L-6-v2`

A cross-encoder reads the query and candidate passage together, producing a
relevance score that captures fine-grained semantic interaction — something
bi-encoders (vector similarity) cannot do.

**Why MiniLM over alternatives:**
- **Cohere Rerank API**: Requires separate API key, adds network latency,
  costs money per query
- **BGE-Reranker-v2**: Higher quality but 4× larger (1.3GB), slower on CPU
- **MiniLM**: ~80MB, ~50ms per pair on CPU, trained on MS MARCO (the standard
  passage ranking benchmark), good balance of quality and speed

**Tradeoff:** Adds ~500ms to total query latency (10 candidates × 50ms). Acceptable
for this use case but could be made optional or async for latency-sensitive
deployments.

### 7. Prompt Design

The system instruction enforces four constraints:
1. **Source grounding** — only use information from retrieved chunks
2. **Citation** — reference specific job IDs and companies
3. **Structured output** — overall assessment + per-job breakdown
4. **Honest about gaps** — say when nothing matches

The context window is capped at 5 chunks (~5,000 chars) to keep the prompt
focused and reduce LLM latency. Each chunk is formatted as `[Source: LF#### -
Title at Company (Location)]` for clear attribution.

Temperature is set to 0.3 to minimize hallucination — RAG answers should be
deterministic and evidence-based, not creative.

## Module Map

| Module | File | Responsibility |
|---|---|---|
| Config | `app/config.py` | Pydantic BaseSettings from `.env` |
| Preprocessing | `app/core/preprocessing.py` | CSV load, HTML clean, section-aware chunking |
| Embeddings | `app/core/embeddings.py` | OpenAI-compatible embeddings wrapper (Ollama/nomic by default) |
| Vector Store | `app/core/vector_store.py` | Qdrant create/search/upsert with payload indexes |
| Retriever | `app/core/retriever.py` | BM25 index + hybrid search + RRF fusion |
| Reranker | `app/core/reranker.py` | Cross-encoder MiniLM reranker |
| LLM | `app/core/llm.py` | OpenAI-compatible LLM (DeepSeek by default) |
| Ingestion | `app/pipeline/ingest.py` | CSV → Qdrant end-to-end orchestrator |
| Query | `app/pipeline/query.py` | Query → answer end-to-end orchestrator |
| API | `app/api/router.py`, `app/api/schemas.py` | FastAPI routes + Pydantic validation |
| App | `app/main.py` | Lifespan hooks, BM25 index init, router mount |
