"""Standalone Groq connectivity/auth test for local debugging.

Usage:
    python Nyaya_AI/scripts/test_groq_connectivity.py
    python Nyaya_AI/scripts/test_groq_connectivity.py --prompt "laws for murder"
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure local imports work when run from repo root.
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

from core.llm.groq_runtime_client import (  # noqa: E402
    GroqRuntimeError,
    load_groq_config,
    request_completion,
    validate_groq_config,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Groq auth and completion endpoint.")
    parser.add_argument(
        "--prompt",
        default="Give a one-line summary of Indian murder law.",
        help="Prompt to send to Groq.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional model override for this run (e.g., llama-3.1-8b-instant).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging for this test run.",
    )
    args = parser.parse_args()

    config = load_groq_config(debug_override=args.debug)
    if args.model:
        config.model = args.model.strip()

    print("=== Groq Connectivity Test ===")
    print(f"API key detected: {'yes' if bool(config.api_key) else 'no'}")
    print(f"Model: {config.model}")
    print(f"Base URL: {config.base_url}")
    print(f"Timeout: {config.timeout_seconds}s")

    try:
        validate_groq_config(config)
    except GroqRuntimeError as exc:
        print(f"Config validation failed: {exc}")
        return 1

    try:
        result = request_completion(prompt=args.prompt, config=config)
    except GroqRuntimeError as exc:
        print("Request failed.")
        print(f"Reason: {exc}")
        if exc.status_code is not None:
            print(f"HTTP status: {exc.status_code}")
        if exc.response_body:
            print(f"Response body: {exc.response_body[:500]}")
        return 2

    print("Request successful.")
    print("Response status: 200")
    print(f"Response model: {result.get('model')}")
    print("Model output:")
    print(result.get("content") or "<empty>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

