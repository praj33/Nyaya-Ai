"""Hybrid query understanding with Groq LLM + local fallback."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List
from urllib import error, request

from dotenv import load_dotenv, find_dotenv

_dotenv_path = find_dotenv(usecwd=False)
load_dotenv(_dotenv_path or None)

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "for", "from",
    "get", "give", "help", "how", "i", "if", "in", "is", "it", "me", "my", "of",
    "on", "or", "please", "the", "to", "under", "what", "when", "where", "which",
    "who", "why", "with", "would", "should", "could", "tell", "about", "need",
}


def analyze_query_llm(query: str) -> Dict[str, Any]:
    """Analyze query via Groq LLM."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY missing")

    model = os.getenv("GROQ_QUERY_UNDERSTANDING_MODEL", "llama-3.1-8b-instant").strip()
    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    timeout_seconds = float(os.getenv("GROQ_TIMEOUT_SECONDS", "20"))

    prompt = "\n".join(
        [
            "You are a legal query analysis system.",
            "",
            "Analyze the following legal question and extract structured information.",
            "",
            "Return JSON with:",
            "",
            "* intent",
            "* domain (criminal, civil, family, property, labour, constitutional)",
            "* keywords",
            "",
            "Question:",
            f"{query}",
            "",
            "Return ONLY JSON.",
        ]
    )

    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "system",
                    "content": "Return concise JSON only. Do not add commentary.",
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
    parsed = _extract_json_object(content)
    if not isinstance(parsed, dict):
        raise ValueError("LLM did not return JSON object")

    return _normalize_llm_output(parsed)


def analyze_query_fallback(query: str) -> Dict[str, Any]:
    """Local rule-based fallback analyzer."""
    query_lower = query.lower()

    domain = "civil"
    if _contains_any(query_lower, ["divorce", "marriage", "custody", "domestic violence", "abuse", "dowry", "cruelty", "beating"]):
        domain = "family"
    elif _contains_any(query_lower, ["theft", "assault", "murder", "rape", "robbery", "fir", "arrest"]):
        domain = "criminal"
    elif _contains_any(query_lower, ["property", "land", "tenant", "title deed", "sale deed"]):
        domain = "property"
    elif _contains_any(query_lower, ["salary", "wages", "employment", "termination", "boss"]):
        domain = "labour"
    elif _contains_any(query_lower, ["constitution", "fundamental rights", "article 14", "article 21"]):
        domain = "constitutional"
    elif _contains_any(query_lower, ["contract", "agreement", "breach", "civil suit"]):
        domain = "civil"

    keywords = _extract_keywords(query_lower)

    return {
        "intent": "general legal inquiry",
        "domain": domain,
        "keywords": keywords,
        "source": "local_fallback",
        "model": None,
    }


def analyze_query(query: str) -> Dict[str, Any]:
    """Hybrid query analysis with LLM first, fallback on failure."""
    try:
        result = analyze_query_llm(query)
        result["source"] = "groq"
        result["model"] = "llama-3.1-8b-instant"
        return result
    except Exception as exc:
        logger.warning("LLM unavailable — using local fallback classifier. Reason: %s", exc)
        return analyze_query_fallback(query)


def _extract_json_object(content: str) -> Dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(text[start : end + 1])


def _normalize_llm_output(payload: Dict[str, Any]) -> Dict[str, Any]:
    intent = str(payload.get("intent", "")).strip() or "general legal inquiry"
    domain = str(payload.get("domain", "")).strip().lower() or "civil"
    keywords = payload.get("keywords", [])
    if not isinstance(keywords, list):
        keywords = []
    cleaned_keywords: List[str] = []
    for value in keywords:
        if isinstance(value, str):
            token = value.strip().lower()
            if token and token not in cleaned_keywords:
                cleaned_keywords.append(token)

    return {
        "intent": intent,
        "domain": domain,
        "keywords": cleaned_keywords[:12],
    }


def _extract_keywords(query_lower: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]+", query_lower)
    keywords: List[str] = []
    for token in tokens:
        if token in _STOPWORDS or len(token) <= 2:
            continue
        if token not in keywords:
            keywords.append(token)
    return keywords[:12]


def _contains_any(text: str, keywords: List[str]) -> bool:
    for keyword in keywords:
        if keyword in text:
            return True
    return False
