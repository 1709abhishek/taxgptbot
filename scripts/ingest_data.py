#!/usr/bin/env python3
"""CLI script for bulk data ingestion."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import argparse
from app.ingestion import CSVParser, PDFParser, PPTParser, GraphBuilder
from app.retrieval import get_vector_store, get_graph_store, get_embedding_service


def main():
    parser = argparse.ArgumentParser(description="Ingest financial documents")
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Files to ingest (CSV, PDF, PPT)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before ingesting",
    )
    args = parser.parse_args()

    # Initialize stores
    vector_store = get_vector_store()
    graph_store = get_graph_store()
    embedding_service = get_embedding_service()
    graph_builder = GraphBuilder()

    if args.clear:
        print("Clearing existing data...")
        vector_store.clear()
        graph_store.clear()

    total_chunks = 0
    total_entities = 0

    for file_path in args.files:
        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue

        print(f"Processing: {file_path.name}")

        # Select parser
        suffix = file_path.suffix.lower()
        if suffix == ".csv":
            parser_instance = CSVParser()
        elif suffix == ".pdf":
            parser_instance = PDFParser()
        elif suffix in (".ppt", ".pptx"):
            parser_instance = PPTParser()
        else:
            print(f"  Unsupported file type: {suffix}")
            continue

        # Read and parse
        content = file_path.read_bytes()
        chunks = parser_instance.parse(content, file_path.name)
        print(f"  Created {len(chunks)} chunks")
        total_chunks += len(chunks)

        # Generate embeddings
        print("  Generating embeddings...")
        texts = [chunk["content"] for chunk in chunks]
        embeddings = embedding_service.embed(texts)

        # Store in vector DB
        for chunk, embedding in zip(chunks, embeddings):
            vector_store.add(
                chunk_id=chunk["chunk_id"],
                content=chunk["content"],
                embedding=embedding,
                metadata=chunk["metadata"],
            )

        # Extract entities and build graph
        print("  Extracting entities...")
        extractions = graph_builder.extract_entities(chunks)
        for extraction in extractions:
            entities = extraction.get("entities", [])
            total_entities += len(entities)
            graph_store.add_extraction(extraction)

    # Persist
    vector_store.persist()
    graph_store.persist()

    print(f"\nDone!")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Total entities: {total_entities}")
    print(f"  Vector store count: {vector_store.count()}")
    print(f"  Graph nodes: {graph_store.node_count()}")
    print(f"  Graph edges: {graph_store.edge_count()}")


if __name__ == "__main__":
    main()
