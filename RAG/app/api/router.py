from fastapi import APIRouter, Request

from app.api.schemas import (
    HealthResponse,
    QueryRequest,
    QueryResponse,
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
