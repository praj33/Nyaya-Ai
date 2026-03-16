from __future__ import annotations

from typing import Any, Dict, Iterable, List


def normalize_issue_values(values: Iterable[Any]) -> List[str]:
    """Normalize issue/profile values for deterministic matching.

    - lowercases
    - trims whitespace
    - collapses internal whitespace
    - preserves underscores (so act_ids still match)
    """
    if not values:
        return []

    normalized: List[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value).strip().lower()
        if not text:
            continue
        text = " ".join(text.split())
        if text not in normalized:
            normalized.append(text)
    return normalized


def build_issue_priority_map(values: Any) -> Dict[str, int]:
    """Build a priority map from ordered values or an explicit mapping."""
    if not values:
        return {}

    if isinstance(values, dict):
        mapping: Dict[str, int] = {}
        for key, weight in values.items():
            if key is None:
                continue
            normalized = normalize_issue_values([key])
            if not normalized:
                continue
            try:
                score = int(weight)
            except (TypeError, ValueError):
                score = 1
            current = mapping.get(normalized[0], 0)
            mapping[normalized[0]] = max(current, score)
        return mapping

    items = normalize_issue_values(values if isinstance(values, list) else [values])
    total = len(items)
    mapping: Dict[str, int] = {}
    for idx, item in enumerate(items):
        score = total - idx
        current = mapping.get(item, 0)
        mapping[item] = max(current, score)
    return mapping
