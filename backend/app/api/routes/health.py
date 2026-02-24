from fastapi import APIRouter, Depends
from app.api.schemas import HealthResponse
from app.retrieval.vector_store import get_vector_store
from app.retrieval.graph_store import get_graph_store

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health and return statistics."""
    vector_store = get_vector_store()
    graph_store = get_graph_store()

    return HealthResponse(
        status="healthy",
        vector_count=vector_store.count(),
        graph_nodes=graph_store.node_count(),
        graph_edges=graph_store.edge_count(),
        last_ingestion=graph_store.last_updated,
    )
