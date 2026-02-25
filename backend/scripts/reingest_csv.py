#!/usr/bin/env python3
"""Re-ingest CSV data with improved chunking for better retrieval."""

import sys
sys.path.insert(0, "/Users/abhishekjain/taxgptbot/backend")

from app.retrieval.vector_store import VectorStore
from app.retrieval.embeddings import EmbeddingService
from app.ingestion.csv_parser import CSVParser

CSV_PATH = "/Users/abhishekjain/taxgptbot/dataset/tax_data_taxgpt.csv"

def main():
    print("=== Re-ingesting CSV with improved chunking ===\n")

    # Initialize services
    vector_store = VectorStore()
    embedding_service = EmbeddingService()
    csv_parser = CSVParser()

    # Step 1: Delete existing CSV chunks
    print("Step 1: Removing existing CSV chunks...")
    collection = vector_store._collection

    # Get all chunks from the CSV file
    results = collection.get(
        where={"source_file": "tax_data_taxgpt.csv"}
    )

    if results and results['ids']:
        print(f"  Found {len(results['ids'])} existing CSV chunks")
        collection.delete(ids=results['ids'])
        print(f"  Deleted {len(results['ids'])} chunks")
    else:
        print("  No existing CSV chunks found")

    # Step 2: Parse CSV with improved chunking
    print("\nStep 2: Parsing CSV with improved chunking...")
    with open(CSV_PATH, "rb") as f:
        content = f.read()

    chunks = csv_parser.parse(content, "tax_data_taxgpt.csv")
    print(f"  Created {len(chunks)} chunks:")
    for chunk in chunks:
        chunk_type = chunk.get('metadata', {}).get('chunk_type', 'unknown')
        print(f"    - {chunk_type}: {len(chunk['content'])} chars")

    # Step 3: Embed and store chunks (in batches due to API limits)
    print("\nStep 3: Embedding chunks...")
    texts = [chunk['content'] for chunk in chunks]

    # Embed in small batches to avoid token limits
    batch_size = 8
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"  Embedding batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}...")
        batch_embeddings = embedding_service.embed(batch)
        embeddings.extend(batch_embeddings)

    print(f"  Generated {len(embeddings)} embeddings")

    # Step 4: Add to vector store
    print("\nStep 4: Adding to vector store...")
    chunk_ids = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"csv_{i}_{chunk.get('metadata', {}).get('chunk_type', 'chunk')}"
        chunk_ids.append(chunk_id)
        metadatas.append({
            "source_file": "tax_data_taxgpt.csv",
            "chunk_type": chunk.get('metadata', {}).get('chunk_type', 'unknown'),
            **{k: v for k, v in chunk.get('metadata', {}).items() if k != 'chunk_type'}
        })

    vector_store.add_batch(
        chunk_ids=chunk_ids,
        contents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    print(f"  Added {len(chunk_ids)} chunks to vector store")

    # Step 5: Verify
    print("\nStep 5: Verifying...")
    results = collection.get(
        where={"source_file": "tax_data_taxgpt.csv"}
    )
    print(f"  CSV chunks in store: {len(results['ids'])}")

    # Test retrieval
    print("\nStep 6: Testing retrieval for 'taxpayer types'...")
    test_query = "What are the different taxpayer types in the tax data?"
    query_embedding = embedding_service.embed([test_query])[0]

    search_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where={"source_file": "tax_data_taxgpt.csv"}
    )

    print(f"  Top results:")
    for i, (doc, meta) in enumerate(zip(search_results['documents'][0], search_results['metadatas'][0])):
        print(f"    {i+1}. [{meta.get('chunk_type', 'unknown')}] {doc[:100]}...")

    print("\n=== CSV re-ingestion complete! ===")

if __name__ == "__main__":
    main()
