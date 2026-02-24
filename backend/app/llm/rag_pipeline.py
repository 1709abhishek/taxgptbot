import json
from typing import Dict, Any, List

from .client import ClaudeClient
from .prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE, ENTITY_EXTRACTION_PROMPT
from app.retrieval.hybrid import HybridRetriever, RetrievalResult
from app.retrieval.vector_store import get_vector_store
from app.retrieval.graph_store import get_graph_store
from app.retrieval.embeddings import get_embedding_service


class RAGPipeline:
    """Full RAG pipeline: query → retrieve → generate."""

    def __init__(self):
        self.client = ClaudeClient()
        self.retriever = HybridRetriever(
            vector_store=get_vector_store(),
            graph_store=get_graph_store(),
            embedding_service=get_embedding_service(),
        )

    def process(self, query: str) -> Dict[str, Any]:
        """
        Process a user query through the full RAG pipeline.

        Returns:
            Dict with answer, confidence, sources, graph_path, retrieval_debug
        """
        # 1. Extract entities from query for graph search
        entities = self._extract_query_entities(query)

        # 2. Retrieve relevant context
        retrieval = self.retriever.retrieve(
            query=query,
            entities=entities,
            top_k=5,
        )

        results = retrieval["results"]
        debug = retrieval["debug"]

        # 3. Build context for LLM
        context = self._build_context(results)
        graph_context = self._build_graph_context(results)

        # 4. Generate answer
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context,
            graph_context=graph_context,
            question=query,
        )

        answer = self.client.chat(
            messages=[{"role": "user", "content": prompt}],
            system=SYSTEM_PROMPT,
        )

        # 5. Calculate confidence based on retrieval quality
        confidence = self._calculate_confidence(results)

        # 6. Format sources
        sources = self._format_sources(results)

        # 7. Get graph path from top result
        graph_path = self._get_graph_path(results)

        return {
            "answer": answer,
            "confidence": confidence,
            "sources": sources,
            "graph_path": graph_path,
            "retrieval_debug": debug,
        }

    def _extract_query_entities(self, query: str) -> List[str]:
        """Use Claude to extract entities from the query."""
        try:
            prompt = ENTITY_EXTRACTION_PROMPT.format(query=query)
            response = self.client.complete(prompt, max_tokens=500)

            # Parse JSON response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                entities = []
                entities.extend(data.get("companies", []))
                entities.extend(data.get("metrics", []))
                entities.extend(data.get("periods", []))
                return entities
        except Exception:
            pass

        return []

    def _build_context(self, results: List[RetrievalResult]) -> str:
        """Build context string from retrieval results."""
        context_parts = []

        for i, result in enumerate(results, 1):
            source = result.source
            metadata = result.metadata
            page = metadata.get("page", "")
            page_str = f" (page {page})" if page else ""

            context_parts.append(
                f"[Source {i}: {source}{page_str}]\n{result.content}\n"
            )

        return "\n".join(context_parts)

    def _build_graph_context(self, results: List[RetrievalResult]) -> str:
        """Build graph context from results with graph paths."""
        graph_parts = []

        for result in results:
            if result.graph_path:
                path_str = self._format_graph_path(result.graph_path)
                graph_parts.append(path_str)

        if not graph_parts:
            return "No graph relationships found."

        return "\n".join(graph_parts)

    def _format_graph_path(self, path: List[Dict[str, Any]]) -> str:
        """Format a graph path for display."""
        parts = []
        for item in path:
            if "node" in item:
                value = item.get("value")
                if value:
                    parts.append(f"{item['node']} ({value})")
                else:
                    parts.append(item["node"])
            elif "edge" in item:
                parts.append(f"-[{item['edge']}]->")

        return " ".join(parts)

    def _calculate_confidence(self, results: List[RetrievalResult]) -> float:
        """Calculate confidence score based on retrieval quality."""
        if not results:
            return 0.0

        # Average of top result scores (normalized to 0-1)
        scores = [r.score for r in results[:3]]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Boost if we have both vector and graph results
        has_vector = any(r.retrieval_type == "vector" for r in results)
        has_graph = any(r.retrieval_type == "graph" for r in results)

        if has_vector and has_graph:
            avg_score = min(avg_score * 1.1, 1.0)

        return round(avg_score, 2)

    def _format_sources(self, results: List[RetrievalResult]) -> List[Dict[str, Any]]:
        """Format retrieval results as source citations."""
        sources = []

        for result in results:
            source = {
                "file": result.source,
                "snippet": result.content[:500],  # Truncate long content
                "chunk_id": result.metadata.get("chunk_id", "unknown"),
            }

            if "page" in result.metadata:
                source["page"] = result.metadata["page"]

            sources.append(source)

        return sources

    def _get_graph_path(self, results: List[RetrievalResult]) -> List[Dict[str, Any]]:
        """Get graph path from results."""
        for result in results:
            if result.graph_path:
                return result.graph_path

        return []
