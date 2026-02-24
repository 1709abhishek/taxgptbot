"""Tests for the ingestion pipeline."""

import pytest
from io import BytesIO
import pandas as pd

from app.ingestion.csv_parser import CSVParser
from app.ingestion.chunker import TextChunker


class TestCSVParser:
    """Tests for CSV parser."""

    def test_parse_simple_csv(self):
        """Test parsing a simple CSV file."""
        csv_content = b"name,value,period\nRevenue,100M,Q1 2024\nProfit,20M,Q1 2024"
        parser = CSVParser()

        chunks = parser.parse(csv_content, "test.csv")

        assert len(chunks) > 0
        assert all("chunk_id" in chunk for chunk in chunks)
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)

    def test_csv_creates_table_chunk(self):
        """Test that CSV parser creates a full table chunk."""
        csv_content = b"col1,col2\na,1\nb,2"
        parser = CSVParser()

        chunks = parser.parse(csv_content, "test.csv")

        # Should have table chunk + row chunks
        table_chunks = [c for c in chunks if c["metadata"]["type"] == "table"]
        assert len(table_chunks) == 1
        assert "Full table" in table_chunks[0]["content"]


class TestTextChunker:
    """Tests for text chunker."""

    def test_short_text_single_chunk(self):
        """Short text should result in single chunk."""
        chunker = TextChunker(chunk_size=500, overlap=50)
        text = "This is a short text."

        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_multiple_chunks(self):
        """Long text should be split into multiple chunks."""
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = "This is sentence one. " * 20

        chunks = chunker.chunk(text)

        assert len(chunks) > 1

    def test_empty_text(self):
        """Empty text should return empty list."""
        chunker = TextChunker()
        chunks = chunker.chunk("")
        assert len(chunks) == 0


class TestPDFParser:
    """Tests for PDF parser - requires actual PDF files."""

    @pytest.mark.skip(reason="Requires PDF test file")
    def test_parse_pdf(self):
        """Test parsing a PDF file."""
        pass


class TestPPTParser:
    """Tests for PPT parser - requires actual PPT files."""

    @pytest.mark.skip(reason="Requires PPT test file")
    def test_parse_ppt(self):
        """Test parsing a PPT file."""
        pass
