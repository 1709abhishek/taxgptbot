from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache
import gc
import chromadb

from app.config import get_settings


@dataclass
class VectorResult:
    """Result from vector search."""

    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class VectorStore:
    """ChromaDB vector store for document chunks."""

    def __init__(self, persist_dir: str = None):
        settings = get_settings()
        self.settings = settings
        persist_dir = persist_dir or settings.chroma_persist_dir

        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name="financial_docs",
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        chunk_id: str,
        content: str,
        embedding: List[float],
        metadata: Dict[str, Any] = None,
    ) -> None:
        """Add a document chunk to the store."""
        self._collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata or {}],
        )

    def add_batch(
        self,
        chunk_ids: List[str],
        contents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]] = None,
        batch_size: int = None,
    ) -> None:
        """
        Add multiple document chunks in a single operation.
        Much faster than individual adds for large datasets.

        Uses smaller batches in low_memory_mode to reduce peak memory.
        """
        if not chunk_ids:
            return

        if metadatas is None:
            metadatas = [{} for _ in chunk_ids]

        # Use settings-based batch size (500 in low memory, 5000 normal)
        if batch_size is None:
            batch_size = self.settings.vector_batch_size

        for i in range(0, len(chunk_ids), batch_size):
            end = i + batch_size
            self._collection.add(
                ids=chunk_ids[i:end],
                embeddings=embeddings[i:end],
                documents=contents[i:end],
                metadatas=metadatas[i:end],
            )

            # GC after each batch in low memory mode
            if self.settings.low_memory_mode:
                gc.collect()

    def search(
        self,
        query_embedding: List[float],
        k: int = 10,
        filter_metadata: Dict[str, Any] = None,
    ) -> List[VectorResult]:
        """Search for similar documents."""
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"],
        )

        vector_results = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # Convert distance to similarity score
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                # Convert to similarity: 0 = opposite, 1 = identical
                distance = results["distances"][0][i]
                score = max(0, 1 - (distance / 2))  # Normalize to 0-1

                vector_results.append(
                    VectorResult(
                        chunk_id=chunk_id,
                        content=results["documents"][0][i],
                        score=score,
                        metadata=results["metadatas"][0][i],
                    )
                )

        return vector_results

    def count(self) -> int:
        """Get total number of documents in the store."""
        return self._collection.count()

    def persist(self) -> None:
        """Persist the store (ChromaDB auto-persists, but call for consistency)."""
        pass

    def delete(self, chunk_ids: List[str]) -> None:
        """Delete documents by ID."""
        self._collection.delete(ids=chunk_ids)

    def clear(self) -> None:
        """Clear all documents from the store."""
        self._client.delete_collection("financial_docs")
        self._collection = self._client.get_or_create_collection(
            name="financial_docs",
            metadata={"hnsw:space": "cosine"},
        )


@lru_cache
def get_vector_store() -> VectorStore:
    """Get singleton vector store."""
    return VectorStore()
