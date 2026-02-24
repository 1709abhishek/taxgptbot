from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class Source(BaseModel):
    file: str
    page: Optional[int] = None
    snippet: str
    chunk_id: str


class GraphNode(BaseModel):
    node: str
    type: str
    value: Optional[str] = None


class GraphEdge(BaseModel):
    edge: str
    direction: str


class RetrievalDebug(BaseModel):
    vector_results: int
    graph_results: int
    rrf_fused: int


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[Source]
    graph_path: list[GraphNode | GraphEdge]
    retrieval_debug: RetrievalDebug
    conversation_id: str


class IngestResponse(BaseModel):
    status: str
    documents_processed: int
    chunks_created: int
    entities_extracted: int
    graph_edges_created: int
    processing_time_seconds: float


class IngestTaskResponse(BaseModel):
    """Response for async ingestion task creation."""
    task_id: str
    filename: str
    status: str
    message: str


class IngestProgressResponse(BaseModel):
    """Progress information for an ingestion task."""
    task_id: str
    filename: str
    status: str
    progress_percent: float
    total_pages: int
    parsed_pages: int
    total_chunks: int
    embedded_chunks: int
    stored_chunks: int
    entities_extracted: int
    edges_created: int
    error_message: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    elapsed_seconds: float


class HealthResponse(BaseModel):
    status: str
    vector_count: int
    graph_nodes: int
    graph_edges: int
    last_ingestion: Optional[datetime] = None
