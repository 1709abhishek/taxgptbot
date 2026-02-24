#!/usr/bin/env python3
"""
Build a sample-based knowledge graph from existing vector store chunks.
Extracts entities from a representative sample to avoid massive API costs.
"""

import sys
import random
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.retrieval.vector_store import get_vector_store
from app.retrieval.graph_store import get_graph_store
from app.ingestion.graph_builder import GraphBuilder


def get_sample_chunks(vector_store, sample_size: int = 300) -> list:
    """
    Get a representative sample of chunks from the vector store.
    Prioritizes chunks with meaningful content (not just headers/metadata).
    """
    collection = vector_store._collection
    total = collection.count()
    print(f"Total chunks in vector store: {total}")

    if total == 0:
        return []

    # Get a larger pool to filter from
    pool_size = min(total, sample_size * 20)
    result = collection.get(
        include=["documents", "metadatas"],
        limit=pool_size,
    )

    # Filter for chunks with meaningful content
    meaningful_chunks = []
    min_content_length = 100  # Skip very short chunks

    for doc_id, content, metadata in zip(
        result["ids"],
        result["documents"],
        result["metadatas"]
    ):
        if not content or len(content) < min_content_length:
            continue

        # Skip chunks that are mostly table headers or metadata
        content_lower = content.lower()
        is_metadata = (
            content_lower.startswith("csv data summary") or
            content_lower.startswith("table of contents") or
            content.count("|") > content.count(" ") / 10  # Mostly table markup
        )

        if not is_metadata:
            meaningful_chunks.append({
                "chunk_id": doc_id,
                "content": content,
                "metadata": metadata or {},
            })

    print(f"Found {len(meaningful_chunks)} meaningful chunks (filtered from {pool_size})")

    # Group by filename for diversity
    by_file = {}
    for chunk in meaningful_chunks:
        filename = chunk["metadata"].get("filename", "unknown")
        if filename not in by_file:
            by_file[filename] = []
        by_file[filename].append(chunk)

    print(f"From {len(by_file)} different files")

    # Sample proportionally from each file
    sampled = []
    files = list(by_file.keys())
    chunks_per_file = max(1, sample_size // max(len(files), 1))

    for filename in files:
        file_chunks = by_file[filename]
        n_sample = min(len(file_chunks), chunks_per_file)
        sampled.extend(random.sample(file_chunks, n_sample))

    # Shuffle and return
    random.shuffle(sampled)
    return sampled[:sample_size]


def build_graph_from_samples(sample_size: int = 300, batch_size: int = 10):
    """
    Build knowledge graph from a sample of chunks.

    Args:
        sample_size: Number of chunks to sample (default 300)
        batch_size: Process in batches to show progress
    """
    print(f"\n{'='*60}")
    print("SAMPLE-BASED GRAPH BUILDER")
    print(f"{'='*60}\n")

    settings = get_settings()
    vector_store = get_vector_store()
    graph_store = get_graph_store()
    graph_builder = GraphBuilder()

    # Get sample chunks
    print(f"Sampling {sample_size} representative chunks...")
    chunks = get_sample_chunks(vector_store, sample_size)

    if not chunks:
        print("No chunks found in vector store!")
        return

    print(f"Got {len(chunks)} chunks for entity extraction\n")

    # Process in batches
    total_entities = 0
    total_edges = 0
    processed = 0
    failed = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(chunks) + batch_size - 1) // batch_size

        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)...")

        try:
            extractions = graph_builder.extract_entities(batch)

            for extraction in extractions:
                entities = extraction.get("entities", [])
                relationships = extraction.get("relationships", [])

                if entities or relationships:
                    graph_store.add_extraction(extraction)
                    total_entities += len(entities)
                    total_edges += len(relationships)

            processed += len(batch)
            print(f"  ✓ Extracted {total_entities} entities, {total_edges} relationships so far")

        except Exception as e:
            failed += len(batch)
            print(f"  ✗ Batch failed: {e}")

    # Persist the graph
    print(f"\nPersisting graph...")
    graph_store.persist()

    # Summary
    print(f"\n{'='*60}")
    print("GRAPH BUILD COMPLETE")
    print(f"{'='*60}")
    print(f"Chunks processed: {processed}")
    print(f"Chunks failed: {failed}")
    print(f"Total entities: {total_entities}")
    print(f"Total relationships: {total_edges}")
    print(f"Graph nodes: {graph_store.node_count()}")
    print(f"Graph edges: {graph_store.edge_count()}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build sample-based knowledge graph")
    parser.add_argument(
        "--sample-size",
        type=int,
        default=300,
        help="Number of chunks to sample (default: 300)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for processing (default: 10)"
    )

    args = parser.parse_args()

    build_graph_from_samples(
        sample_size=args.sample_size,
        batch_size=args.batch_size,
    )
