from abc import ABC, abstractmethod
from typing import List, Dict, Any
import uuid


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, content: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Parse document content into chunks.

        Returns:
            List of dictionaries with:
                - chunk_id: Unique identifier
                - content: Text content
                - metadata: Dict with source info (filename, page, type, etc.)
        """
        pass

    def _generate_chunk_id(self) -> str:
        """Generate a unique chunk ID."""
        return f"chunk_{uuid.uuid4().hex[:12]}"

    def _create_chunk(
        self,
        content: str,
        filename: str,
        page: int = None,
        chunk_type: str = "text",
        extra_metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Create a standardized chunk dictionary."""
        metadata = {
            "filename": filename,
            "type": chunk_type,
        }
        if page is not None:
            metadata["page"] = page
        if extra_metadata:
            metadata.update(extra_metadata)

        return {
            "chunk_id": self._generate_chunk_id(),
            "content": content,
            "metadata": metadata,
        }
