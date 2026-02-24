from typing import List, Dict, Any
from dataclasses import dataclass

from .vector_store import VectorStore, VectorResult
from .graph_store import GraphStore, GraphResult
from .embeddings import EmbeddingService


@dataclass
class RetrievalResult:
    """Unified result from hybrid retrieval."""

    content: str
    source: str
    score: float
    retrieval_type: str  # "vector" or "graph"
    metadata: Dict[str, Any]
    graph_path: List[Dict[str, Any]] = None


class HybridRetriever:
    """
    Combines vector search and graph traversal for retrieval.
    Uses Reciprocal Rank Fusion (RRF) for merging results.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        graph_store: GraphStore,
        embedding_service: EmbeddingService,
    ):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedding_service = embedding_service

    def retrieve(
        self,
        query: str,
        entities: List[str] = None,
        top_k: int = 5,
        vector_weight: float = 0.6,
        graph_weight: float = 0.4,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context using both vector and graph search.

        Args:
            query: User query
            entities: Extracted entities from query (optional)
            top_k: Number of results to return
            vector_weight: Weight for vector results in fusion
            graph_weight: Weight for graph results in fusion

        Returns:
            Dict with results and debug info
        """
        # Vector search
        query_embedding = self.embedding_service.embed_query(query)
        vector_results = self.vector_store.search(query_embedding, k=top_k * 2)

        # Graph search
        graph_results = self.graph_store.search(query, entities=entities, k=top_k * 2)

        # Convert to unified format
        vector_unified = [
            RetrievalResult(
                content=r.content,
                source=r.metadata.get("filename", "unknown"),
                score=r.score,
                retrieval_type="vector",
                metadata=r.metadata,
            )
            for r in vector_results
        ]

        graph_unified = [
            RetrievalResult(
                content=r.content,
                source=r.metadata.get("source_file", "unknown"),
                score=r.score,
                retrieval_type="graph",
                metadata=r.metadata,
                graph_path=r.path,
            )
            for r in graph_results
        ]

        # RRF Fusion
        fused = self._rrf_fusion(
            vector_unified,
            graph_unified,
            vector_weight=vector_weight,
            graph_weight=graph_weight,
        )

        return {
            "results": fused[:top_k],
            "debug": {
                "vector_results": len(vector_results),
                "graph_results": len(graph_results),
                "rrf_fused": len(fused),
            },
        }

    def _rrf_fusion(
        self,
        vector_results: List[RetrievalResult],
        graph_results: List[RetrievalResult],
        k: int = 60,
        vector_weight: float = 0.6,
        graph_weight: float = 0.4,
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion for combining rankings.

        RRF score = sum(weight / (k + rank))
        """
        scores: Dict[str, Dict[str, Any]] = {}

        # Score vector results
        for rank, result in enumerate(vector_results):
            key = result.content[:200]  # Use content prefix as key
            if key not in scores:
                scores[key] = {"result": result, "score": 0}
            scores[key]["score"] += vector_weight / (k + rank + 1)

        # Score graph results
        for rank, result in enumerate(graph_results):
            key = result.content[:200]
            if key not in scores:
                scores[key] = {"result": result, "score": 0}
            else:
                # If exists from vector, preserve graph path
                if result.graph_path:
                    scores[key]["result"].graph_path = result.graph_path
            scores[key]["score"] += graph_weight / (k + rank + 1)

        # Sort by fused score
        sorted_results = sorted(
            scores.values(), key=lambda x: x["score"], reverse=True
        )

        # Keep original similarity scores (for confidence), RRF is just for ranking
        # Don't overwrite result.score with RRF score
        return [item["result"] for item in sorted_results]
