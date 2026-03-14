"""Query preprocessing utilities for Nyaya AI."""

from __future__ import annotations

import re


def clean_query(query: str) -> str:
    """Normalize user queries before any retrieval or reasoning.

    - lowercase
    - remove punctuation
    - keep alphanumerics + spaces
    - normalize whitespace
    """
    if query is None:
        return ""

    text = str(query).lower()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = " ".join(text.split())
    return text.strip()
