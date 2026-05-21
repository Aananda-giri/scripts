# RAG Pipeline for Job Data Retrieval

Retrieval-Augmented Generation (RAG) pipeline over 1,000 job listings. Given a natural
language query, the system retrieves the most relevant job descriptions and generates a
concise, source-grounded answer via an OpenAI-compatible LLM (DeepSeek by default).

## Architecture

```
User Query
    │
    ▼
┌──────────────────────────────────────────────────┐
│  FastAPI (POST /api/query)                       │
│    ├─ Query embedding   (nomic-embed-text-v1.5 via Ollama)
│    ├─ Vector search     (Qdrant)                  │
│    ├─ Keyword search    (BM25)                    │
│    ├─ RRF fusion        (k=60)                    │
│    ├─ Cross-encoder     (ms-marco-MiniLM-L-6-v2)  │
│    └─ LLM generation    (DeepSeek-Chat)           │
└──────────────────────────────────────────────────┘
    │
    ▼
Structured JSON response (answer + ranked jobs + metadata)
```

### Retrieval Pipeline

Three-stage retrieval for maximum precision:

| Stage | Method | Top-K | Purpose |
|---|---|---|---|
| 1a | Cosine similarity on dense embeddings (Qdrant) | 20 | Semantic understanding |
| 1b | BM25 keyword search (rank-bm25) | 20 | Exact term matching |
| 2 | Reciprocal Rank Fusion (k=60) | 10 | Combines both rankings |
| 3 | Cross-encoder reranker | 5 | Fine-grained relevance scoring |

### Chunking Strategy

Job descriptions are chunked semantically by section headings (Responsibilities, Skills,
Qualifications, etc.), not by fixed character windows. This ensures each chunk contains
a coherent unit of information. Chunks are 1,000 chars max with 200-char overlap.

### Data Flow (Ingestion)

```
CSV → HTML clean → Section detection → Chunk → Embed (Ollama / nomic) → Qdrant upsert
                                                    ↘ BM25 index (in-memory)
```

---

## Setup

### Prerequisites

- Python 3.12+
- Docker (for Qdrant)
- Ollama running locally ([install](https://ollama.com)) with `nomic-embed-text` pulled
- A DeepSeek API key ([get one](https://platform.deepseek.com/api_keys)) — or any OpenAI-compatible provider

### Installation

```bash
# 1. Start Qdrant
docker compose up -d qdrant

# 2. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_COMPATIBLE_API_KEY

# 5. Ingest data
python scripts/ingest.py "LF Jobs - LF Jobs.csv"

# 6. Start the API
uvicorn app.main:app --reload --port 8000
```

### Docker (Full Stack)

```bash
OPENAI_COMPATIBLE_API_KEY=your-key docker compose up --build
```

This starts both Qdrant and the API. The app automatically indexes the CSV on first
startup. Ingestion takes 2-3 minutes for all 1,000 jobs.

---

## API Usage

### `POST /api/query`

Search for jobs using natural language.

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "senior python developer in new york",
    "top_k": 3,
    "include_sources": true,
    "filters": {
      "job_level": ["Senior Level"],
      "job_category": ["Software Engineering"]
    }
  }'
```

**Request fields:**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | yes | — | Natural language query (3-500 chars) |
| `top_k` | int | no | 5 | Number of results (1-10) |
| `include_sources` | bool | no | true | Include raw chunk text in response |
| `filters` | object | no | null | Optional facet filters |

**Filter fields (all optional, all accept arrays):**
`job_category`, `job_level`, `company_name`, `job_location`

**Example response:**

```json
{
  "query": "senior python developer in new york",
  "answer": "I found 2 senior software engineering roles in New York matching your query...",
  "results": [
    {
      "job_id": "LF0042",
      "job_title": "Senior Software Engineer",
      "company": "Google",
      "location": "New York, NY",
      "job_level": "Senior Level",
      "job_category": "Software Engineering",
      "relevance_score": 0.8912,
      "section_type": "requirements",
      "source_text": "We are looking for a Senior Software Engineer..."
    }
  ],
  "processing_time_ms": 1523,
  "retrieval_details": {
    "fused_count": 10,
    "reranked_count": 5,
    "retrieval_time_ms": 710,
    "generation_time_ms": 813
  }
}
```

### `GET /api/health`

```bash
curl http://localhost:8000/api/health
```

Returns Qdrant connection status, collection point count, and active LLM model.

---

## Example Queries

| Query | Expected behavior |
|---|---|
| "Software engineering roles in the bay area" | SWE positions at tech companies in CA |
| "Data analytics internship summer 2025" | Internship + Data and Analytics |
| "Senior project manager with healthcare experience" | Senior PM at CVS, Cigna, etc. |
| "Marketing positions in London" | Advertising/Marketing with London location |
| "Entry level python developer remote" | Entry/Internship mentioning Python |

---

## Assumptions

1. **Qdrant runs locally via Docker.** The app connects to `localhost:6333` by default.
2. **Ollama is running locally with the nomic-embed-text model pulled.** Embeddings run entirely on your machine with no API cost.
3. **The CSV is well-formed.** HTML in job descriptions is stripped with BeautifulSoup. Missing locations (9 rows) are imputed as "Location Not Specified".
4. **BM25 index is in-memory.** At ~6,000 chunks, memory usage is under 500MB. Not suitable for millions of documents without redesign.
5. **Cross-encoder model is downloaded at startup.** First run downloads ~80MB from Hugging Face.
6. **Single-user API.** No authentication, rate limiting, or multi-tenancy is implemented.

---

## Drawbacks & Future Enhancements

### Current Limitations

- **In-memory BM25 index** is lost on restart and must be rebuilt. For production, persist the index or use Qdrant's built-in sparse vector support.
- **Cross-encoder adds ~500ms latency** per query. This is a quality-vs-speed tradeoff; it can be disabled for lower latency.
- **No caching.** Repeated queries re-run the full pipeline (embedding, search, rerank, LLM generation).
- **No metadata filter pushdown to BM25.** Filters only apply to the vector search leg; BM25 returns results across all categories.
- **Static dataset.** New job listings require manual re-ingestion.

### Potential Enhancements

- **Query expansion** — use the LLM to generate 2-3 query variants before retrieval, improving recall for ambiguous queries.
- **Persistent BM25** — use Qdrant's upcoming sparse vector API or an external index (Elasticsearch) for hybrid search at scale.
- **Streaming responses** — stream LLM tokens to the client for faster time-to-first-byte.
- **User feedback loop** — log click-through on results to fine-tune the reranker.
- **Faceted search UI** — add a simple frontend for browsing categories, levels, and locations.
- **Scheduled re-ingestion** — periodically re-index the CSV or connect to a live job feed.
