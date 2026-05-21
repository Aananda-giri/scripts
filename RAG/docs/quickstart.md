# Quickstart

Get the RAG pipeline running in under 5 minutes.

## Prerequisites

- Python 3.12+
- Docker
- Ollama with `nomic-embed-text` pulled: `ollama pull nomic-embed-text`
- A DeepSeek API key (or any OpenAI-compatible provider key)

## 1. Start Qdrant

```bash
docker compose up -d qdrant
```

Verify it's healthy:

```bash
curl http://localhost:6333/health
```

## 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configure

```bash
cp .env.example .env
```

Edit `.env` and set your key:

```
OPENAI_COMPATIBLE_API_KEY=your-actual-key
```

The defaults for Qdrant host/port and model selection work out of the box.

## 4. Ingest the dataset

```bash
python scripts/ingest.py "LF Jobs - LF Jobs.csv"
```

This will:
1. Load 1,000 job listings from CSV
2. Clean HTML and split into semantic chunks (~6,000 total)
3. Generate embeddings locally via Ollama (nomic-embed-text-v1.5)
4. Upsert everything into Qdrant

Expected output:

```
Loading and chunking: LF Jobs - LF Jobs.csv
Total chunks: 6247
Generating embeddings (batch_size=50)...
Generated 6247 embeddings
Upserted 6247 points to Qdrant collection 'job_chunks'
Collection info: {'name': 'job_chunks', 'points_count': 6247, ...}
```

## 5. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

## 6. Run your first query

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "senior data scientist with python in new york"}'
```

### With filters

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "cloud architect",
    "top_k": 5,
    "filters": {
      "job_level": ["Senior Level"],
      "job_category": ["Software Engineering"]
    }
  }'
```

### Health check

```bash
curl http://localhost:8000/api/health
```

## Docker (all-in-one)

Skip steps 1-5 and run everything in containers:

```bash
OPENAI_COMPATIBLE_API_KEY=your-key docker compose up --build
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `Connection refused` on :6333 | Qdrant container not running: `docker compose up -d qdrant` |
| `Connection refused` on :11434 | Ollama not running. Start it with `ollama serve` or `docker compose up -d ollama`. |
| Empty results | Data wasn't ingested. Run `python scripts/ingest.py` first. |
| `ModuleNotFoundError` | Virtual env not activated or deps not installed. |
| Cross-encoder download hangs | First run downloads ~80MB from Hugging Face. Needs internet. |
