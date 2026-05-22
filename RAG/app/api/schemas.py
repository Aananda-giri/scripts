from pydantic import BaseModel, Field


class QueryFilters(BaseModel):
    job_category: list[str] | None = None
    job_level: list[str] | None = None
    company_name: list[str] | None = None
    job_location: list[str] | None = None


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=10)
    include_sources: bool = True
    filters: QueryFilters | None = None


class JobResult(BaseModel):
    job_id: str
    job_title: str
    company: str
    location: str
    job_level: str
    job_category: str
    relevance_score: float
    section_type: str = ""
    source_text: str = ""


class RetrievalMetadata(BaseModel):
    fused_count: int
    reranked_count: int
    retrieval_time_ms: int
    generation_time_ms: int


class QueryResponse(BaseModel):
    query: str
    search_query: str = ""
    extracted_filters: dict = {}
    answer: str = ""
    results: list[JobResult]
    processing_time_ms: int
    retrieval_details: RetrievalMetadata


class SearchResponse(BaseModel):
    query: str
    search_query: str = ""
    extracted_filters: dict = {}
    results: list[JobResult]
    processing_time_ms: int
    retrieval_details: RetrievalMetadata


class HealthResponse(BaseModel):
    status: str
    qdrant: dict
    model: str
