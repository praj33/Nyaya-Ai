"""Production-ready Groq runtime client with strong diagnostics.

This module is intentionally standalone so it can be used for both:
1) direct connectivity/auth testing
2) application runtime calls
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, request

from dotenv import find_dotenv, load_dotenv


DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
DEFAULT_TIMEOUT_SECONDS = 20.0


@dataclass
class GroqConfig:
    api_key: str
    model: str = DEFAULT_GROQ_MODEL
    base_url: str = DEFAULT_GROQ_BASE_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    debug: bool = False


class GroqRuntimeError(RuntimeError):
    """Raised for Groq runtime request failures."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_body: str = "",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


def _mask_key(value: str) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 10:
        return f"{value[:2]}***"
    return f"{value[:6]}...{value[-4:]}"


def _sanitize_key(raw_key: Optional[str]) -> str:
    value = (raw_key or "").strip()
    # Common copy/paste issue from env files and shell exports.
    value = value.strip('"').strip("'").strip()
    return value


def _validate_key(api_key: str) -> Optional[str]:
    if not api_key:
        return "GROQ_API_KEY is missing."
    if "\n" in api_key or "\r" in api_key or "\t" in api_key:
        return "GROQ_API_KEY has hidden control characters."
    if " " in api_key:
        return "GROQ_API_KEY contains spaces."
    if not api_key.startswith("gsk_"):
        return "GROQ_API_KEY does not start with expected prefix 'gsk_'."
    if len(api_key) < 20:
        return "GROQ_API_KEY looks too short."
    return None


def load_groq_config(*, debug_override: Optional[bool] = None) -> GroqConfig:
    """Load Groq config from environment with robust .env discovery."""
    dotenv_path = find_dotenv(usecwd=False)
    load_dotenv(dotenv_path or None)

    # Fallback for running scripts from repo root.
    if not os.getenv("GROQ_API_KEY"):
        fallback_env = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        )
        if os.path.exists(fallback_env):
            load_dotenv(fallback_env, override=False)

    raw_key = os.getenv("GROQ_API_KEY")
    api_key = _sanitize_key(raw_key)
    model = (os.getenv("GROQ_MODEL") or DEFAULT_GROQ_MODEL).strip()
    base_url = (os.getenv("GROQ_BASE_URL") or DEFAULT_GROQ_BASE_URL).rstrip("/")
    timeout_str = (os.getenv("GROQ_TIMEOUT_SECONDS") or str(DEFAULT_TIMEOUT_SECONDS)).strip()
    debug_env = (os.getenv("GROQ_DEBUG") or "false").strip().lower()
    debug = debug_env not in {"0", "false", "no"}
    if debug_override is not None:
        debug = debug_override

    try:
        timeout_seconds = float(timeout_str)
    except ValueError:
        timeout_seconds = DEFAULT_TIMEOUT_SECONDS

    return GroqConfig(
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        debug=debug,
    )


def validate_groq_config(config: GroqConfig) -> None:
    issue = _validate_key(config.api_key)
    if issue:
        raise GroqRuntimeError(issue)


def _build_headers(config: GroqConfig) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "NyayaAI/1.0",
    }


def _request_chat_completion(
    *,
    config: GroqConfig,
    messages: list[dict[str, str]],
    temperature: float = 0.1,
) -> Dict[str, Any]:
    endpoint = f"{config.base_url}/chat/completions"
    payload = json.dumps(
        {
            "model": config.model,
            "messages": messages,
            "temperature": temperature,
        }
    ).encode("utf-8")
    req = request.Request(
        endpoint,
        data=payload,
        headers=_build_headers(config),
        method="POST",
    )

    if config.debug:
        print(f"[groq] API key detected: {_mask_key(config.api_key)}")
        print(f"[groq] Request endpoint: {endpoint}")
        print(f"[groq] Request model: {config.model}")
        print("[groq] Request being sent...")

    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
            if config.debug:
                print(f"[groq] Response status: {response.status}")
            return json.loads(response_body)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        if config.debug:
            print(f"[groq] HTTP error status: {exc.code}")
            print(f"[groq] HTTP error body: {body[:500]}")
        raise GroqRuntimeError(
            f"Groq HTTP error: {exc.code}",
            status_code=exc.code,
            response_body=body,
        ) from exc
    except error.URLError as exc:
        if config.debug:
            print(f"[groq] URL/network error: {exc}")
        raise GroqRuntimeError(f"Groq network error: {exc}") from exc
    except OSError as exc:
        if config.debug:
            print(f"[groq] OS/socket error: {exc}")
        raise GroqRuntimeError(f"Groq socket error: {exc}") from exc


def request_completion(
    *,
    prompt: str,
    system_prompt: str = (
        "You are a concise legal AI assistant. Use only grounded, factual language."
    ),
    config: Optional[GroqConfig] = None,
) -> Dict[str, Any]:
    """Perform a single Groq chat completion call."""
    cfg = config or load_groq_config()
    validate_groq_config(cfg)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    data = _request_chat_completion(config=cfg, messages=messages, temperature=0.1)

    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )

    return {
        "status": "ok",
        "model": data.get("model", cfg.model),
        "content": content,
        "raw": data,
    }

