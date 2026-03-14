"""Query expansion with Groq LLM + local fallback."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import List
from urllib import error, request

from dotenv import load_dotenv, find_dotenv

_dotenv_path = find_dotenv(usecwd=False)
load_dotenv(_dotenv_path or None)

logger = logging.getLogger(__name__)


def expand_query_llm(query: str, domain: str) -> List[str]:
    """Expand a query using Groq LLM."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY missing")

    model = os.getenv("GROQ_QUERY_EXPANDER_MODEL", "llama-3.1-8b-instant").strip()
    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    timeout_seconds = float(os.getenv("GROQ_TIMEOUT_SECONDS", "20"))

    prompt = "\n".join(
        [
            "You are a legal search query generator.",
            "",
            "A user asked the following legal question:",
            f"{query}",
            "",
            "Legal domain:",
            f"{domain}",
            "",
            "Generate 4 alternative legal search queries that would help retrieve relevant laws or case precedents.",
            "",
            "Return only a JSON list of queries.",
        ]
    )

    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": "Return JSON list only. Do not add commentary.",
                },
                {"role": "user", "content": prompt},
            ],
        }
    ).encode("utf-8")

    req = request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "NyayaAI/1.0",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=timeout_seconds) as response:
        data = json.loads(response.read().decode("utf-8"))

    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    parsed = _extract_json_list(content)
    normalized = _normalize_queries(parsed)
    if not normalized:
        raise ValueError("LLM returned empty query list")
    return normalized[:4]


def expand_query_fallback(query: str, domain: str) -> List[str]:
    """Fallback expansion when LLM is unavailable."""
    base = (query or "").strip()
    expanded = [
        base,
        f"{base} law India",
        f"{base} legal rights",
        f"{base} court procedure",
    ]
    return _normalize_queries(expanded)[:4]


def expand_query(query: str, domain: str) -> List[str]:
    """Expand query with LLM first, fallback on failure."""
    try:
        return expand_query_llm(query, domain)
    except Exception as exc:
        logger.warning("Query expansion LLM failed - using fallback. Reason: %s", exc)
        return expand_query_fallback(query, domain)


def _extract_json_list(content: str) -> List[str]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON list found in LLM response")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, list):
        raise ValueError("LLM did not return JSON list")
    return parsed


def _normalize_queries(items: List[str]) -> List[str]:
    deduped: List[str] = []
    seen = set()
    for item in items:
        if not isinstance(item, str):
            continue
        cleaned = " ".join(item.split())
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
    return deduped
