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
        # Vector search with source diversity
        # Fetch from each source type separately to ensure diversity
        query_embedding = self.embedding_service.embed_query(query)
        vector_results = self._search_with_diversity(query_embedding, k=top_k * 2)

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

    def _search_with_diversity(
        self, query_embedding: List[float], k: int
    ) -> List[VectorResult]:
        """
        Search with smart source diversity.

        Strategy:
        1. First get global top results (best matches across all sources)
        2. Check if minority sources (CSV, PPT) have high-scoring results
        3. Only inject minority results if they score above threshold AND
           that source type isn't already represented

        This ensures:
        - PDF queries get PDF results (not forced CSV)
        - CSV queries get CSV results (injected if missing from global top)
        """
        # Step 1: Get global top results without any filtering
        global_results = self.vector_store.search(query_embedding, k=k * 2)

        # Check what sources are already represented in top results
        sources_in_results = set()
        for r in global_results[:k]:
            source = r.metadata.get("source_file", "")
            sources_in_results.add(source)

        # Step 2: Check minority sources for high-scoring results
        minority_sources = [
            {"source_file": "tax_data_taxgpt.csv"},
            {"source_file": "MIC_3e_Ch11_taxgpt.ppt"},
        ]

        # Minimum score threshold to inject (must be reasonably relevant)
        MIN_SCORE_THRESHOLD = 0.65

        injected_results = []
        for source_filter in minority_sources:
            source_file = source_filter["source_file"]

            # Skip if this source is already in global results
            if source_file in sources_in_results:
                continue

            try:
                # Get top result from this minority source
                source_results = self.vector_store.search(
                    query_embedding,
                    k=2,
                    filter_metadata=source_filter
                )

                # Only inject if score is above threshold
                for r in source_results:
                    if r.score >= MIN_SCORE_THRESHOLD:
                        injected_results.append(r)
            except Exception:
                pass

        # Step 3: Merge global results with injected minority results
        all_results = list(global_results) + injected_results

        # Remove duplicates by content
        seen_content = set()
        unique_results = []
        for r in all_results:
            content_key = r.content[:200]
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(r)

        # Sort by score and return top k
        unique_results.sort(key=lambda x: x.score, reverse=True)
        return unique_results[:k]
