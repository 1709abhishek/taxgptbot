#!/usr/bin/env python3
"""Evaluation script for the RAG pipeline."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import json
from app.llm.rag_pipeline import RAGPipeline
from app.retrieval import get_vector_store, get_graph_store


def load_eval_dataset(path: Path) -> dict:
    """Load evaluation dataset."""
    with open(path) as f:
        return json.load(f)


def evaluate(eval_file: Path = None):
    """Run evaluation on the RAG pipeline."""
    if eval_file is None:
        eval_file = Path(__file__).parent.parent / "backend/tests/eval_dataset.json"

    if not eval_file.exists():
        print(f"Evaluation file not found: {eval_file}")
        print("Create an eval_dataset.json with Q&A pairs to run evaluation.")
        return

    data = load_eval_dataset(eval_file)
    pipeline = RAGPipeline()

    results = {
        "recall@5": 0,
        "mrr@5": 0,
        "citation_accuracy": 0,
        "total": 0,
    }

    for q in data.get("questions", []):
        question = q["question"]
        expected_source = q.get("source_file")

        print(f"\nQ: {question}")

        # Get answer
        result = pipeline.process(question)

        print(f"A: {result['answer'][:200]}...")
        print(f"Confidence: {result['confidence']:.2f}")

        # Check recall (correct source in top 5)
        sources = result.get("sources", [])
        source_files = [s.get("file") for s in sources]

        if expected_source and expected_source in source_files:
            results["recall@5"] += 1
            # MRR calculation
            rank = source_files.index(expected_source)
            results["mrr@5"] += 1 / (rank + 1)
            print(f"  Source found at rank {rank + 1}")
        else:
            print(f"  Expected source not found: {expected_source}")

        results["total"] += 1

    # Calculate metrics
    if results["total"] > 0:
        n = results["total"]
        print(f"\n{'='*50}")
        print(f"EVALUATION RESULTS ({n} questions)")
        print(f"{'='*50}")
        print(f"Recall@5: {results['recall@5']/n:.2%}")
        print(f"MRR@5: {results['mrr@5']/n:.3f}")

    # Print store stats
    vector_store = get_vector_store()
    graph_store = get_graph_store()
    print(f"\nStore Statistics:")
    print(f"  Vector count: {vector_store.count()}")
    print(f"  Graph nodes: {graph_store.node_count()}")
    print(f"  Graph edges: {graph_store.edge_count()}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate RAG pipeline")
    parser.add_argument(
        "--eval-file",
        type=Path,
        help="Path to evaluation dataset JSON",
    )
    args = parser.parse_args()

    evaluate(args.eval_file)
