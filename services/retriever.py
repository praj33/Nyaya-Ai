"""Hybrid legal retrieval using BM25 + FAISS vector search."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

try:
    from rank_bm25 import BM25Okapi
    from sentence_transformers import SentenceTransformer
    import faiss
    _IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - optional dependency guard
    BM25Okapi = None
    SentenceTransformer = None
    faiss = None
    _IMPORT_ERROR = exc

logger = logging.getLogger(__name__)


class HybridLegalRetriever:
    """Hybrid retrieval over statute records using BM25 and vector similarity."""

    def __init__(self, data_path: Path | None = None):
        self.data_path = data_path or self._default_data_path()
        self.records: List[Dict[str, Any]] = self._load_records(self.data_path)
        self._bm25_corpus: List[List[str]] = []
        self._bm25: Any = None
        self._embedding_model: Any = None
        self._faiss_index: Any = None
        self._embeddings: np.ndarray | None = None
        self._build_indexes()

    def _default_data_path(self) -> Path:
        repo_root = Path(__file__).resolve().parents[2]
        return repo_root / "data" / "statutes.json"

    def _load_records(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            logger.warning("Statute dataset not found at %s, attempting DB fallback", path)
            records = self._build_records_from_db()
            if records:
                self._persist_records(path, records)
                return records
            raise FileNotFoundError(f"Statute dataset not found at {path}")
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Statute dataset must be a list of records")
        if not _has_pocso(data):
            logger.warning("Statute dataset missing POCSO entries, rebuilding from DB")
            records = self._build_records_from_db()
            if records:
                self._persist_records(path, records)
                return records
        return data

    def _build_records_from_db(self) -> List[Dict[str, Any]]:
        try:
            from data_bridge.loader import JSONLoader
        except ImportError:
            from Nyaya_AI.data_bridge.loader import JSONLoader

        repo_root = Path(__file__).resolve().parents[2]
        db_path = repo_root / "Nyaya_AI" / "db"
        if not db_path.exists():
            logger.warning("DB path not found for fallback: %s", db_path)
            return []

        loader = JSONLoader(str(db_path))
        sections, acts, _cases = loader.load_and_normalize_directory(str(db_path))
        act_map = {act.act_id: act for act in acts}

        records: List[Dict[str, Any]] = []
        for section in sections:
            act = act_map.get(section.act_id)
            act_name = act.act_name if act else section.act_id
            year = act.year if act else _infer_year_from_id(section.act_id)
            metadata = section.metadata or {}
            title = (
                metadata.get("title")
                or metadata.get("heading")
                or metadata.get("offence")
                or metadata.get("description")
                or section.text[:120]
            )
            records.append(
                {
                    "act": act_name,
                    "year": year,
                    "section": section.section_number,
                    "title": title,
                    "text": section.text,
                    "domain": metadata.get("domain") or _infer_domain_from_act_id(section.act_id),
                }
            )

        return records

    def _persist_records(self, path: Path, records: List[Dict[str, Any]]) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            logger.info("Persisted fallback statute dataset to %s", path)
        except Exception as exc:
            logger.warning("Failed to persist fallback statute dataset: %s", exc)

    def _build_indexes(self) -> None:
        if _IMPORT_ERROR:
            raise RuntimeError(
                "Hybrid retriever dependencies missing. Install rank-bm25, sentence-transformers, faiss-cpu."
            ) from _IMPORT_ERROR
        corpus_tokens: List[List[str]] = []
        texts: List[str] = []
        for record in self.records:
            title = str(record.get("title", ""))
            text = str(record.get("text", ""))
            corpus_text = f"{title} {text}".strip()
            texts.append(corpus_text)
            corpus_tokens.append(self._tokenize(corpus_text))

        self._bm25_corpus = corpus_tokens
        self._bm25 = BM25Okapi(self._bm25_corpus)

        self._embedding_model = SentenceTransformer("BAAI/bge-m3")
        embeddings = self._embedding_model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        self._embeddings = np.asarray(embeddings, dtype="float32")

        dim = self._embeddings.shape[1]
        self._faiss_index = faiss.IndexFlatIP(dim)
        self._faiss_index.add(self._embeddings)

    def bm25_search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if not self._bm25:
            return []
        tokens = self._tokenize(query)
        scores = self._bm25.get_scores(tokens)
        top_indices = np.argsort(scores)[::-1][:top_k]
        results: List[Tuple[Dict[str, Any], float]] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0:
                continue
            results.append((self.records[idx], score))
        return results

    def vector_search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        if not self._faiss_index or not self._embedding_model:
            return []
        query_vec = self._embedding_model.encode(
            [query], normalize_embeddings=True
        ).astype("float32")
        scores, indices = self._faiss_index.search(query_vec, top_k)
        results: List[Tuple[Dict[str, Any], float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append((self.records[int(idx)], float(score)))
        return results

    def hybrid_search(self, queries: List[str], top_k: int = 10) -> Dict[str, Any]:
        combined: Dict[str, Dict[str, Any]] = {}
        per_query_logs: List[Dict[str, Any]] = []

        for query in queries:
            bm25_hits = self.bm25_search(query, top_k=top_k)
            vector_hits = self.vector_search(query, top_k=top_k)

            per_query_logs.append(
                {
                    "query": query,
                    "bm25_hits": len(bm25_hits),
                    "vector_hits": len(vector_hits),
                }
            )
            logger.info(
                'query="%s" bm25_hits=%s vector_hits=%s',
                query,
                len(bm25_hits),
                len(vector_hits),
            )

            for record, score in bm25_hits:
                key = self._record_key(record)
                bucket = combined.setdefault(
                    key, {"record": record, "bm25": 0.0, "vector": 0.0}
                )
                bucket["bm25"] = max(bucket["bm25"], score)

            for record, score in vector_hits:
                key = self._record_key(record)
                bucket = combined.setdefault(
                    key, {"record": record, "bm25": 0.0, "vector": 0.0}
                )
                bucket["vector"] = max(bucket["vector"], score)

        ranked = sorted(
            combined.values(),
            key=lambda item: item["bm25"] + item["vector"],
            reverse=True,
        )

        top_ranked = ranked[:top_k]
        candidates = [self._record_summary(item["record"]) for item in top_ranked]
        candidate_records = [item["record"] for item in top_ranked]

        return {
            "candidates": candidates,
            "candidate_records": candidate_records,
            "sections_found": len(candidates),
            "query_logs": per_query_logs,
        }

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [token for token in text.lower().split() if token.strip()]

    @staticmethod
    def _record_key(record: Dict[str, Any]) -> str:
        return "|".join(
            [
                str(record.get("act", "")).lower(),
                str(record.get("year", "")),
                str(record.get("section", "")).lower(),
            ]
        )

    @staticmethod
    def _record_summary(record: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "act": record.get("act"),
            "year": record.get("year"),
            "section": record.get("section"),
            "title": record.get("title"),
        }


def _infer_domain_from_act_id(act_id: str) -> str:
    act = (act_id or "").lower()
    if any(key in act for key in ["ipc", "bns", "crpc", "bnss", "uapa", "crime", "penal", "it_act", "pocso"]):
        return "criminal"
    if any(key in act for key in ["hindu_marriage", "special_marriage", "domestic_violence", "dowry"]):
        return "family"
    if any(key in act for key in ["consumer"]):
        return "consumer"
    if any(key in act for key in ["income_tax", "cgst", "tax"]):
        return "tax"
    if any(key in act for key in ["labour", "wage", "employment"]):
        return "employment"
    if any(key in act for key in ["property", "real_estate", "limitation", "cpc", "transfer"]):
        return "civil_property"
    return "civil"


def _infer_year_from_id(act_id: str) -> int:
    import re

    match = re.search(r"\b(19|20)\d{2}\b", act_id or "")
    if match:
        return int(match.group(0))
    return 0


def _has_pocso(records: List[Dict[str, Any]]) -> bool:
    for record in records:
        act = str(record.get("act", "")).lower()
        if "children from sexual offences" in act or "pocso" in act:
            return True
    return False


_RETRIEVER: HybridLegalRetriever | None = None


def get_hybrid_retriever() -> HybridLegalRetriever:
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = HybridLegalRetriever()
    return _RETRIEVER
