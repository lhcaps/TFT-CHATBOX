"""Ranking service for reordering retrieval results."""
from __future__ import annotations

from typing import Any


def rerank_chunks(chunks: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """Reorder chunks by relevance to query (simple TF-IDF heuristic)."""
    query_terms = set(query.lower().split())

    def score(chunk: dict[str, Any]) -> float:
        content_lower = chunk["content"].lower()
        term_hits = sum(1 for term in query_terms if term in content_lower)
        return term_hits / max(len(query_terms), 1) + chunk.get("similarity", 0)

    return sorted(chunks, key=score, reverse=True)
