from typing import List
import re


class TextChunker:
    """Split text into overlapping chunks for embedding."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        """
        Split text into chunks, respecting sentence boundaries where possible.
        """
        # Clean text
        text = self._clean_text(text)

        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        chunks = []
        sentences = self._split_sentences(text)

        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text) if overlap_text else 0

            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space

        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap(self, chunks: List[str]) -> str:
        """Get overlap text from the end of chunks."""
        if not chunks:
            return ""

        # Take last few sentences up to overlap size
        overlap_text = ""
        for sentence in reversed(chunks):
            if len(overlap_text) + len(sentence) <= self.overlap:
                overlap_text = sentence + " " + overlap_text
            else:
                break

        return overlap_text.strip()
