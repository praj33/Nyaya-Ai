"""Rerank candidate statutes using a cross-encoder reranker."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

try:
    from sentence_transformers import CrossEncoder
    _IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - optional dependency guard
    CrossEncoder = None
    _IMPORT_ERROR = exc

logger = logging.getLogger(__name__)

_RERANKER: Any = None


def _get_reranker() -> Any:
    global _RERANKER
    if _RERANKER is None:
        if _IMPORT_ERROR:
            raise RuntimeError(
                "Reranker dependency missing. Install sentence-transformers."
            ) from _IMPORT_ERROR
        _RERANKER = CrossEncoder("BAAI/bge-reranker-large")
    return _RERANKER


def rerank_sections(query: str, candidate_sections: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """Rerank candidate statute sections by relevance to the query."""
    if not candidate_sections:
        return []

    reranker = _get_reranker()
    pairs = []
    for candidate in candidate_sections:
        title = str(candidate.get("title", ""))
        text = str(candidate.get("text", ""))
        section = str(candidate.get("section", "")).strip()
        act = str(candidate.get("act", "")).strip()
        section_prefix = f"Section {section} " if section else ""
        act_suffix = f" under {act}" if act else ""
        combined = f"{section_prefix}{title}{act_suffix} {text}".strip()
        pairs.append((query, combined))

    scores = reranker.predict(pairs)
    scored: List[Dict[str, Any]] = []
    for candidate, score in zip(candidate_sections, scores):
        enriched = dict(candidate)
        enriched["rerank_score"] = float(score)
        scored.append(enriched)

    scored.sort(key=lambda item: item.get("rerank_score", 0.0), reverse=True)
    return scored[:top_k]
