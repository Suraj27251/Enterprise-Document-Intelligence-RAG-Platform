"""Evaluate retrieval precision@k and average latency for RAG pipeline."""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass

from app.services.llm_service import generate_answer
from app.services.retriever import retrieve_similar_chunks


@dataclass
class EvalExample:
    query: str
    expected_source_substring: str


EXAMPLES = [
    EvalExample(query="Summarize contract renewal terms", expected_source_substring="contract"),
    EvalExample(query="What is the incident response SLA?", expected_source_substring="sla"),
]


def precision_at_k(hits: list[dict[str, str | int | float]], expected_substring: str, k: int = 5) -> float:
    top_hits = hits[:k]
    if not top_hits:
        return 0.0
    relevant = sum(1 for hit in top_hits if expected_substring.lower() in str(hit.get("source", "")).lower())
    return relevant / k


def run_evaluation(output_csv: str = "evaluation_results.csv") -> None:
    rows: list[dict[str, str | float]] = []
    for example in EXAMPLES:
        start = time.perf_counter()
        hits = retrieve_similar_chunks(example.query, top_k=5)
        _ = generate_answer(example.query, hits)
        latency = time.perf_counter() - start
        p_at_5 = precision_at_k(hits, example.expected_source_substring, k=5)
        rows.append({"query": example.query, "precision_at_5": p_at_5, "latency_seconds": round(latency, 3)})

    avg_precision = sum(float(row["precision_at_5"]) for row in rows) / len(rows) if rows else 0.0
    avg_latency = sum(float(row["latency_seconds"]) for row in rows) / len(rows) if rows else 0.0
    rows.append({"query": "AVERAGE", "precision_at_5": round(avg_precision, 3), "latency_seconds": round(avg_latency, 3)})

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["query", "precision_at_5", "latency_seconds"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved evaluation results to {output_csv}")


if __name__ == "__main__":
    run_evaluation()
