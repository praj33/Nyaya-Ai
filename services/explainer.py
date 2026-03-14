"""Groq-backed legal explanation generator with deterministic fallback."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List
from urllib import error, request

from dotenv import load_dotenv, find_dotenv

_dotenv_path = find_dotenv(usecwd=False)
load_dotenv(_dotenv_path or None)

logger = logging.getLogger(__name__)


def generate_explanation(
    query: str, jurisdiction: str, domain: str, statutes: List[Dict[str, Any]]
) -> str:
    """Return explanation text using Groq or fallback."""
    payload = generate_explanation_payload(query, jurisdiction, domain, statutes)
    return payload["text"]


def generate_explanation_payload(
    query: str, jurisdiction: str, domain: str, statutes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Return explanation text + metadata for tracing."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_EXPLAINER_MODEL", "llama-3.1-8b-instant").strip()
    base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    timeout_seconds = float(os.getenv("GROQ_TIMEOUT_SECONDS", "20"))
    enabled = os.getenv("GROQ_ENABLED", "true").lower() not in {"0", "false", "no"}

    statute_context = _build_statute_context(statutes)
    if statute_context == "None provided":
        fallback = (
            "Relevant statutes were not identified from the available corpus. "
            "Please provide more details or consult a legal professional."
        )
    else:
        fallback = (
            "Relevant statutes (deterministic):\n"
            f"{statute_context}\n\n"
            "Please consult a legal professional for detailed advice."
        )

    if statute_context == "None provided":
        logger.warning("Explanation skipped: no statutes provided")
        return {"text": fallback, "source": "local_fallback", "model": None, "reason": "no_statutes"}

    if not enabled or not api_key:
        reason = "GROQ_ENABLED is false" if not enabled else "GROQ_API_KEY missing"
        logger.warning("Explanation LLM unavailable: %s", reason)
        return {"text": fallback, "source": "local_fallback", "model": None, "reason": reason}

    prompt = "\n".join(
        [
            "You are a legal assistant.",
            "",
            "Explain the relevant legal provisions clearly for a citizen.",
            "",
            "IMPORTANT RULES:",
            "",
            "* Only use the statutes provided below.",
            "* Do not invent laws.",
            "* Do not reference statutes that are not listed.",
            "* Do not include helplines, phone numbers, or non-legal resources.",
            "* Keep explanation simple and clear.",
            "",
            "User Question:",
            f"{query}",
            "",
            "Jurisdiction:",
            f"{jurisdiction}",
            "",
            "Relevant Statutes:",
            f"{statute_context}",
            "",
            "Explain what these laws mean for the user and what legal options may exist.",
        ]
    )

    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You must only use the provided statutes. "
                        "If they are insufficient, say so briefly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
    ).encode("utf-8")

    try:
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
        text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if not text:
            raise ValueError("Groq returned empty explanation")
        if not _mentions_any_statute(text, statutes):
            raise ValueError("Groq response did not reference provided statutes")
        if _jurisdiction_mismatch(text, jurisdiction):
            raise ValueError("Groq response referenced the wrong jurisdiction")
        logger.info("Explanation generated successfully")
        return {"text": text, "source": "groq", "model": data.get("model", model)}
    except (ValueError, OSError, error.HTTPError, error.URLError) as exc:
        logger.warning("Explanation generation failed: %s", exc)
        return {
            "text": fallback,
            "source": "local_fallback",
            "model": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _build_statute_context(statutes: List[Dict[str, Any]]) -> str:
    lines = []
    for statute in statutes or []:
        section = statute.get("section", "")
        act = statute.get("act", "")
        year = statute.get("year", "")
        title = statute.get("title", "")
        if section or act:
            line = f"Section {section} of {act} ({year}): {title}".strip()
            lines.append(line)
    return "\n".join(lines) if lines else "None provided"


def _jurisdiction_mismatch(text: str, jurisdiction: str) -> bool:
    if not text:
        return False
    jurisdiction_value = (jurisdiction or "").upper()
    lowered = text.lower()
    us_signals = (
        "united states",
        "u.s.",
        "national domestic violence hotline",
        "1-800",
        "hotline",
        "indiana",
    )
    if jurisdiction_value in {"IN", "INDIA"}:
        return any(signal in lowered for signal in us_signals)
    if jurisdiction_value in {"UK", "UNITED KINGDOM"}:
        return any(signal in lowered for signal in us_signals)
    if jurisdiction_value in {"UAE", "UNITED ARAB EMIRATES"}:
        return any(signal in lowered for signal in us_signals)
    return False


def _mentions_any_statute(text: str, statutes: List[Dict[str, Any]]) -> bool:
    if not text or not statutes:
        return False
    lowered = text.lower()
    for statute in statutes:
        act = str(statute.get("act", "")).strip().lower()
        section = str(statute.get("section", "")).strip().lower()
        if act and act in lowered:
            return True
        if section and f"section {section}" in lowered:
            return True
    return False
