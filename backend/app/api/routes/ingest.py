import gc
import time
import asyncio
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from typing import List, Dict, Any

from app.api.schemas import (
    IngestResponse,
    IngestTaskResponse,
    IngestProgressResponse,
)
from app.config import get_settings
from app.ingestion.csv_parser import CSVParser
from app.ingestion.pdf_parser import PDFParser
from app.ingestion.ppt_parser import PPTParser
from app.ingestion.graph_builder import GraphBuilder
from app.ingestion.progress import (
    get_progress_tracker,
    TaskStatus,
)
from app.retrieval.vector_store import get_vector_store
from app.retrieval.graph_store import get_graph_store
from app.retrieval.embeddings import get_embedding_service

router = APIRouter()


def process_file_background(
    task_id: str,
    content: bytes,
    filename: str,
) -> None:
    """
    Background task for processing large files.
    Updates progress tracker as it processes.

    In low memory mode, uses streaming pipeline:
    parse batch → embed → store → clear → repeat
    """
    settings = get_settings()
    tracker = get_progress_tracker()
    vector_store = get_vector_store()
    graph_store = get_graph_store()
    embedding_service = get_embedding_service()
    graph_builder = GraphBuilder()

    try:
        # Determine parser
        filename_lower = filename.lower()
        if filename_lower.endswith(".csv"):
            parser = CSVParser()
            is_pdf = False
        elif filename_lower.endswith(".pdf"):
            parser = PDFParser()
            is_pdf = True
        elif filename_lower.endswith((".ppt", ".pptx")):
            parser = PPTParser()
            is_pdf = False
        else:
            tracker.fail_task(task_id, f"Unsupported file type: {filename}")
            return

        # Get page count for PDFs
        total_pages = 1
        if is_pdf:
            total_pages = parser.get_page_count(content)
            tracker.update_task(task_id, total_pages=total_pages)

        # Use streaming mode for large PDFs in low memory mode
        use_streaming = (
            is_pdf
            and settings.low_memory_mode
            and total_pages > settings.low_memory_page_batch_size
        )

        if use_streaming:
            _process_pdf_streaming(
                task_id, content, filename, parser,
                tracker, vector_store, graph_store,
                embedding_service, graph_builder, settings,
            )
        else:
            _process_file_standard(
                task_id, content, filename, is_pdf, parser,
                tracker, vector_store, graph_store,
                embedding_service, graph_builder,
            )

        # Persist
        vector_store.persist()
        graph_store.persist()

        # Complete
        tracker.set_status(task_id, TaskStatus.COMPLETED)

    except Exception as e:
        tracker.fail_task(task_id, str(e))
        raise


def _process_pdf_streaming(
    task_id: str,
    content: bytes,
    filename: str,
    parser: PDFParser,
    tracker,
    vector_store,
    graph_store,
    embedding_service,
    graph_builder,
    settings,
) -> None:
    """
    Streaming pipeline for large PDFs in low memory mode.
    Processes page batches one at a time: parse → embed → store → clear.
    """
    total_pages = parser.get_page_count(content)
    total_chunks_processed = 0
    total_entities = 0
    total_edges = 0

    # Calculate total batches
    page_batch_size = settings.low_memory_page_batch_size
    total_batches = (total_pages + page_batch_size - 1) // page_batch_size

    # Mark as streaming mode
    tracker.update_task(
        task_id,
        streaming_mode=True,
        total_batches=total_batches,
        total_chunks=total_pages * 2,  # Estimate
    )

    tracker.set_status(task_id, TaskStatus.PARSING)

    def page_progress(current: int, total: int):
        tracker.update_task(task_id, parsed_pages=current)

    # Stream through page batches
    current_batch = 0
    for batch_chunks in parser.parse_streaming(
        content,
        filename,
        progress_callback=page_progress,
    ):
        current_batch += 1
        batch_size = len(batch_chunks)
        tracker.update_task(task_id, current_batch=current_batch)

        if batch_size == 0:
            continue

        # Update estimated total based on actual chunks seen
        total_chunks_processed += batch_size

        # EMBED this batch
        tracker.set_status(task_id, TaskStatus.EMBEDDING)
        texts = [chunk["content"] for chunk in batch_chunks]

        embeddings = embedding_service.embed_batched(texts)
        tracker.update_task(task_id, embedded_chunks=total_chunks_processed)

        # STORE this batch
        tracker.set_status(task_id, TaskStatus.STORING)
        chunk_ids = [chunk["chunk_id"] for chunk in batch_chunks]
        metadatas = [chunk["metadata"] for chunk in batch_chunks]

        vector_store.add_batch(
            chunk_ids=chunk_ids,
            contents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        tracker.update_task(
            task_id,
            stored_chunks=total_chunks_processed,
            total_chunks=total_chunks_processed,  # Update actual total
        )

        # GRAPH building for this batch
        extractions = graph_builder.extract_entities(batch_chunks)
        for extraction in extractions:
            entities = extraction.get("entities", [])
            relationships = extraction.get("relationships", [])
            total_entities += len(entities)
            total_edges += len(relationships)
            graph_store.add_extraction(extraction)

        tracker.update_task(
            task_id,
            entities_extracted=total_entities,
            edges_created=total_edges,
        )

        # CLEAR memory - critical for low memory mode
        del batch_chunks, texts, embeddings, chunk_ids, metadatas, extractions
        gc.collect()

        # Back to parsing for next batch (if any)
        tracker.set_status(task_id, TaskStatus.PARSING)

    # Final graph building stage marker
    tracker.set_status(task_id, TaskStatus.GRAPH_BUILDING)


def _process_file_standard(
    task_id: str,
    content: bytes,
    filename: str,
    is_pdf: bool,
    parser,
    tracker,
    vector_store,
    graph_store,
    embedding_service,
    graph_builder,
) -> None:
    """
    Standard (non-streaming) processing for smaller files.

    For CSV files, uses deterministic structured graph extraction.
    For PDF/PPT files, uses LLM-based entity extraction.
    """
    # STAGE 1: Parsing
    tracker.set_status(task_id, TaskStatus.PARSING)

    def parsing_progress(current: int, total: int):
        tracker.update_task(
            task_id,
            parsed_pages=current,
            total_pages=total,
        )

    if is_pdf:
        chunks = parser.parse(
            content,
            filename,
            parallel=True,
            progress_callback=parsing_progress,
        )
    else:
        chunks = parser.parse(content, filename)
        tracker.update_task(task_id, parsed_pages=1, total_pages=1)

    total_chunks = len(chunks)
    tracker.update_task(task_id, total_chunks=total_chunks)

    # STAGE 2: Embedding
    tracker.set_status(task_id, TaskStatus.EMBEDDING)

    texts = [chunk["content"] for chunk in chunks]

    def embedding_progress(current: int, total: int):
        tracker.update_task(task_id, embedded_chunks=current)

    embeddings = embedding_service.embed_batched(
        texts,
        progress_callback=embedding_progress,
    )

    # STAGE 3: Storing in vector database
    tracker.set_status(task_id, TaskStatus.STORING)

    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    # Use batch add for efficiency
    vector_store.add_batch(
        chunk_ids=chunk_ids,
        contents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    tracker.update_task(task_id, stored_chunks=total_chunks)

    # STAGE 4: Graph building
    tracker.set_status(task_id, TaskStatus.GRAPH_BUILDING)

    total_entities = 0
    total_edges = 0

    # Use structured extraction for CSV, LLM-based for PDF/PPT
    filename_lower = filename.lower()
    if filename_lower.endswith(".csv"):
        # CSV: Use deterministic structured extraction (no LLM calls, much faster)
        csv_extractions = parser.build_graph_extractions(content, filename)
        for extraction in csv_extractions:
            entities = extraction.get("entities", [])
            relationships = extraction.get("relationships", [])
            total_entities += len(entities)
            total_edges += len(relationships)
            graph_store.add_extraction(extraction)
    else:
        # PDF/PPT: Use LLM-based entity extraction
        extractions = graph_builder.extract_entities(chunks)
        for extraction in extractions:
            entities = extraction.get("entities", [])
            relationships = extraction.get("relationships", [])
            total_entities += len(entities)
            total_edges += len(relationships)
            graph_store.add_extraction(extraction)

    tracker.update_task(
        task_id,
        entities_extracted=total_entities,
        edges_created=total_edges,
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_files(files: List[UploadFile] = File(...)):
    """
    Synchronous ingestion for small files.
    For large PDFs, use /ingest/async instead.
    """
    start_time = time.time()

    vector_store = get_vector_store()
    graph_store = get_graph_store()
    embedding_service = get_embedding_service()
    graph_builder = GraphBuilder()

    total_chunks = 0
    total_entities = 0
    total_edges = 0

    for file in files:
        content = await file.read()
        filename = file.filename.lower()

        # Select parser based on file type
        if filename.endswith(".csv"):
            parser = CSVParser()
        elif filename.endswith(".pdf"):
            parser = PDFParser()
        elif filename.endswith((".ppt", ".pptx")):
            parser = PPTParser()
        else:
            continue

        # Parse document into chunks
        chunks = parser.parse(content, file.filename)
        total_chunks += len(chunks)

        # Generate embeddings in batches
        texts = [chunk["content"] for chunk in chunks]
        embeddings = embedding_service.embed_batched(texts)

        # Batch add to vector store
        chunk_ids = [chunk["chunk_id"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        vector_store.add_batch(
            chunk_ids=chunk_ids,
            contents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        # Build graph - use structured extraction for CSV, LLM for others
        if filename.endswith(".csv"):
            # CSV: Use deterministic structured extraction (no LLM calls)
            csv_extractions = parser.build_graph_extractions(content, file.filename)
            for extraction in csv_extractions:
                entities = extraction.get("entities", [])
                relationships = extraction.get("relationships", [])
                total_entities += len(entities)
                total_edges += len(relationships)
                graph_store.add_extraction(extraction)
        else:
            # PDF/PPT: Use LLM-based entity extraction
            extractions = graph_builder.extract_entities(chunks)
            for extraction in extractions:
                entities = extraction.get("entities", [])
                relationships = extraction.get("relationships", [])
                total_entities += len(entities)
                total_edges += len(relationships)
                graph_store.add_extraction(extraction)

    # Persist stores
    vector_store.persist()
    graph_store.persist()

    processing_time = time.time() - start_time

    return IngestResponse(
        status="success",
        documents_processed=len(files),
        chunks_created=total_chunks,
        entities_extracted=total_entities,
        graph_edges_created=total_edges,
        processing_time_seconds=round(processing_time, 2),
    )


@router.post("/ingest/async", response_model=IngestTaskResponse)
async def ingest_file_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Asynchronous ingestion for large files (especially PDFs).
    Returns immediately with a task_id for progress tracking.

    Use GET /ingest/status/{task_id} to check progress.
    """
    content = await file.read()
    filename = file.filename

    # Validate file type
    filename_lower = filename.lower()
    if not any(
        filename_lower.endswith(ext)
        for ext in [".csv", ".pdf", ".ppt", ".pptx"]
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: CSV, PDF, PPT, PPTX",
        )

    # Create task
    tracker = get_progress_tracker()
    task_id = tracker.create_task(filename)

    # Schedule background processing
    background_tasks.add_task(
        process_file_background,
        task_id,
        content,
        filename,
    )

    return IngestTaskResponse(
        task_id=task_id,
        filename=filename,
        status="pending",
        message="File queued for processing. Use /ingest/status/{task_id} to track progress.",
    )


@router.get("/ingest/status/{task_id}", response_model=IngestProgressResponse)
async def get_ingest_status(task_id: str):
    """
    Get the status and progress of an async ingestion task.
    """
    tracker = get_progress_tracker()
    task = tracker.get_task(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found",
        )

    return IngestProgressResponse(**task.to_dict())


@router.get("/ingest/tasks")
async def list_ingest_tasks():
    """
    List all ingestion tasks and their status.
    """
    tracker = get_progress_tracker()
    return {"tasks": list(tracker.get_all_tasks().values())}
