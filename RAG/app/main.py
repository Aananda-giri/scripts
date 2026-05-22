from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import Settings
from app.core.preprocessing import load_and_chunk
from app.pipeline.query import QueryPipeline
from app.api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    print(f"Using device: {settings.device}")
    pipeline = QueryPipeline(settings)
    print(f"Embedder device: {pipeline.embedder.device}")
    print(f"Reranker device: {pipeline.reranker.device}")

    csv_path = Path(__file__).resolve().parent.parent / "LF Jobs - LF Jobs.csv"
    if csv_path.exists():
        chunks = load_and_chunk(
            str(csv_path),
            max_size=settings.chunk_max_size,
            overlap=settings.chunk_overlap,
            min_size=settings.chunk_min_size,
        )
        pipeline.retriever.build_bm25_index(chunks)

    app.state.pipeline = pipeline
    yield


app = FastAPI(title="Job RAG API", version="1.0.0", lifespan=lifespan)
app.include_router(router)

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
