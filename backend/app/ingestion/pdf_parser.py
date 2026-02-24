import gc
import multiprocessing
from typing import List, Dict, Any, Callable, Optional, Generator
from concurrent.futures import ProcessPoolExecutor, as_completed
import pymupdf

from .base import BaseParser
from .chunker import TextChunker
from app.config import get_settings


def _process_single_page(args: tuple) -> List[Dict[str, Any]]:
    """
    Process a single page - must be a module-level function for multiprocessing.
    Args: (pdf_bytes, filename, page_num, chunk_size, chunk_overlap)
    """
    pdf_bytes, filename, page_num, chunk_size, chunk_overlap = args
    chunks = []
    chunker = TextChunker(chunk_size=chunk_size, overlap=chunk_overlap)

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num - 1]  # 0-indexed

    # Extract tables as markdown
    table_chunks = _extract_tables_from_page(page, filename, page_num)
    chunks.extend(table_chunks)

    # Extract regular text
    text = page.get_text()
    if text.strip():
        text_chunks = _chunk_text(text, filename, page_num, chunker)
        chunks.extend(text_chunks)

    doc.close()
    return chunks


def _extract_tables_from_page(
    page, filename: str, page_num: int
) -> List[Dict[str, Any]]:
    """Extract tables from page and convert to Markdown."""
    chunks = []

    try:
        tables = page.find_tables()
        for table_idx, table in enumerate(tables):
            df = table.to_pandas()

            # Clean up headers (first row often becomes header)
            if len(df) > 0 and df.iloc[0].notna().all():
                df.columns = df.iloc[0]
                df = df[1:]

            if len(df) == 0:
                continue

            markdown = df.to_markdown(index=False)
            chunk_id = f"{filename}_p{page_num}_table{table_idx}"

            chunks.append({
                "chunk_id": chunk_id,
                "content": f"Table from {filename} (page {page_num}):\n\n{markdown}",
                "metadata": {
                    "filename": filename,
                    "page": page_num,
                    "chunk_type": "table",
                    "table_index": table_idx,
                    "headers": list(df.columns),
                },
            })
    except Exception:
        pass

    return chunks


def _chunk_text(
    text: str, filename: str, page_num: int, chunker: TextChunker
) -> List[Dict[str, Any]]:
    """Split text into chunks with overlap."""
    chunks = []
    text_chunks = chunker.chunk(text)

    for idx, chunk_text in enumerate(text_chunks):
        chunk_id = f"{filename}_p{page_num}_chunk{idx}"
        chunks.append({
            "chunk_id": chunk_id,
            "content": chunk_text,
            "metadata": {
                "filename": filename,
                "page": page_num,
                "chunk_type": "text",
                "chunk_index": idx,
            },
        })

    return chunks


class PDFParser(BaseParser):
    """
    Parser for PDF files with parallel processing support.
    Extracts text and converts tables to Markdown for accurate embedding.

    Supports low memory mode for 8GB machines via streaming batch processing.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunker = TextChunker(chunk_size=chunk_size, overlap=chunk_overlap)
        self.settings = get_settings()

    def parse(
        self,
        content: bytes,
        filename: str,
        parallel: bool = True,
        max_workers: int = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Parse PDF content, extracting text and tables.

        Args:
            content: PDF file bytes
            filename: Name of the file
            parallel: Use parallel processing (recommended for large PDFs)
            max_workers: Number of parallel workers (default: from settings)
            progress_callback: Optional callback(current_page, total_pages)

        Returns:
            List of chunk dictionaries
        """
        doc = pymupdf.open(stream=content, filetype="pdf")
        total_pages = len(doc)
        doc.close()

        # Use settings-based max_workers
        if max_workers is None:
            max_workers = self.settings.max_workers

        # For small PDFs, use sequential processing
        if total_pages <= 10 or not parallel:
            return self._parse_sequential(
                content, filename, total_pages, progress_callback
            )

        return self._parse_parallel(
            content, filename, total_pages, max_workers, progress_callback
        )

    def parse_streaming(
        self,
        content: bytes,
        filename: str,
        page_batch_size: int = None,
        max_workers: int = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Stream PDF parsing in page batches for low memory usage.

        Instead of loading all chunks into memory, yields batches of chunks
        that can be processed (embedded + stored) before the next batch.

        Args:
            content: PDF file bytes
            filename: Name of the file
            page_batch_size: Pages per batch (default: from settings)
            max_workers: Parallel workers (default: from settings)
            progress_callback: Optional callback(current_page, total_pages)

        Yields:
            List of chunk dictionaries for each page batch
        """
        doc = pymupdf.open(stream=content, filetype="pdf")
        total_pages = len(doc)
        doc.close()

        if page_batch_size is None:
            page_batch_size = self.settings.low_memory_page_batch_size

        if max_workers is None:
            max_workers = self.settings.max_workers

        # Process in page batches
        pages_processed = 0
        for batch_start in range(1, total_pages + 1, page_batch_size):
            batch_end = min(batch_start + page_batch_size - 1, total_pages)

            # Parse this batch of pages
            batch_chunks = self._parse_page_range(
                content,
                filename,
                batch_start,
                batch_end,
                max_workers,
            )

            pages_processed = batch_end
            if progress_callback:
                progress_callback(pages_processed, total_pages)

            yield batch_chunks

            # Force garbage collection after each batch
            del batch_chunks
            gc.collect()

    def _parse_page_range(
        self,
        content: bytes,
        filename: str,
        start_page: int,
        end_page: int,
        max_workers: int,
    ) -> List[Dict[str, Any]]:
        """
        Parse a specific range of pages.

        Args:
            content: PDF bytes
            filename: File name
            start_page: First page (1-indexed)
            end_page: Last page (1-indexed, inclusive)
            max_workers: Number of parallel workers
        """
        num_pages = end_page - start_page + 1

        # For small batches, use sequential
        if num_pages <= 5 or max_workers <= 1:
            return self._parse_range_sequential(content, filename, start_page, end_page)

        # Parallel processing for this batch
        args_list = [
            (content, filename, page_num, self.chunk_size, self.chunk_overlap)
            for page_num in range(start_page, end_page + 1)
        ]

        all_chunks = []

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_page = {
                executor.submit(_process_single_page, args): args[2]
                for args in args_list
            }

            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    page_chunks = future.result()
                    all_chunks.extend(page_chunks)
                except Exception as e:
                    print(f"Error processing page {page_num}: {e}")

        # Sort by page number
        all_chunks.sort(
            key=lambda x: (x["metadata"]["page"], x["metadata"].get("chunk_index", 0))
        )

        return all_chunks

    def _parse_range_sequential(
        self,
        content: bytes,
        filename: str,
        start_page: int,
        end_page: int,
    ) -> List[Dict[str, Any]]:
        """Sequential parsing for a page range."""
        chunks = []
        doc = pymupdf.open(stream=content, filetype="pdf")

        for page_num in range(start_page, end_page + 1):
            page = doc[page_num - 1]  # 0-indexed

            # Extract tables as markdown
            table_chunks = _extract_tables_from_page(page, filename, page_num)
            chunks.extend(table_chunks)

            # Extract regular text
            text = page.get_text()
            if text.strip():
                text_chunks = _chunk_text(text, filename, page_num, self.chunker)
                chunks.extend(text_chunks)

        doc.close()
        return chunks

    def _parse_sequential(
        self,
        content: bytes,
        filename: str,
        total_pages: int,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Sequential parsing for small PDFs."""
        chunks = []
        doc = pymupdf.open(stream=content, filetype="pdf")

        for page_num, page in enumerate(doc, start=1):
            # Extract tables as markdown
            table_chunks = _extract_tables_from_page(page, filename, page_num)
            chunks.extend(table_chunks)

            # Extract regular text
            text = page.get_text()
            if text.strip():
                text_chunks = _chunk_text(text, filename, page_num, self.chunker)
                chunks.extend(text_chunks)

            if progress_callback:
                progress_callback(page_num, total_pages)

        doc.close()
        return chunks

    def _parse_parallel(
        self,
        content: bytes,
        filename: str,
        total_pages: int,
        max_workers: int = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Parallel parsing for large PDFs using multiprocessing.
        Processes pages in parallel batches for maximum throughput.
        """
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), 8)

        # Prepare arguments for each page
        args_list = [
            (content, filename, page_num, self.chunk_size, self.chunk_overlap)
            for page_num in range(1, total_pages + 1)
        ]

        all_chunks = []
        completed = 0

        # Process in parallel using ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_page = {
                executor.submit(_process_single_page, args): args[2]
                for args in args_list
            }

            # Collect results as they complete
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    page_chunks = future.result()
                    all_chunks.extend(page_chunks)
                except Exception as e:
                    print(f"Error processing page {page_num}: {e}")

                completed += 1
                if progress_callback:
                    progress_callback(completed, total_pages)

        # Sort chunks by page number to maintain order
        all_chunks.sort(
            key=lambda x: (x["metadata"]["page"], x["metadata"].get("chunk_index", 0))
        )

        return all_chunks

    def get_page_count(self, content: bytes) -> int:
        """Get the total number of pages without full parsing."""
        doc = pymupdf.open(stream=content, filetype="pdf")
        count = len(doc)
        doc.close()
        return count
