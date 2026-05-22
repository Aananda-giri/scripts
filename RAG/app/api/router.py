import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SearchResponse,
)

router = APIRouter()


@router.post("/api/query", response_model=QueryResponse)
async def query_jobs(req: QueryRequest, request: Request):
    pipeline = request.app.state.pipeline
    filters = None
    if req.filters:
        filters = {}
        for field in ["job_category", "job_level", "company_name", "job_location"]:
            val = getattr(req.filters, field, None)
            if val:
                filters[field] = val

    result = pipeline.run_query(
        query=req.query,
        top_k=req.top_k,
        filters=filters,
    )

    if not req.include_sources:
        for r in result["results"]:
            r["source_text"] = ""

    return result


@router.post("/api/query/stream")
async def query_jobs_stream(req: QueryRequest, request: Request):
    pipeline = request.app.state.pipeline
    filters = None
    if req.filters:
        filters = {}
        for field in ["job_category", "job_level", "company_name", "job_location"]:
            val = getattr(req.filters, field, None)
            if val:
                filters[field] = val

    def _generate():
        for token in pipeline.run_query_stream(
            query=req.query,
            top_k=req.top_k,
            filters=filters,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")


@router.post("/api/search", response_model=SearchResponse)
async def search_jobs(req: QueryRequest, request: Request):
    pipeline = request.app.state.pipeline
    filters = None
    if req.filters:
        filters = {}
        for field in ["job_category", "job_level", "company_name", "job_location"]:
            val = getattr(req.filters, field, None)
            if val:
                filters[field] = val

    result = pipeline.run_query(
        query=req.query,
        top_k=req.top_k,
        filters=filters,
        skip_generation=True,
    )

    if not req.include_sources:
        for r in result["results"]:
            r["source_text"] = ""

    return result


@router.get("/api/health", response_model=HealthResponse)
async def health(request: Request):
    pipeline = request.app.state.pipeline
    try:
        info = pipeline.vector_store.collection_info()
        qdrant_status = {"connected": True, **info}
    except Exception as e:
        qdrant_status = {"connected": False, "error": str(e)}

    return {
        "status": "healthy" if qdrant_status["connected"] else "degraded",
        "qdrant": qdrant_status,
        "model": pipeline.settings.llm_model,
    }
