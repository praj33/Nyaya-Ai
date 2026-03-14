"""Deterministic legal reasoning rules for statute enrichment."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def apply_reasoning_rules(query: str, domain: str, statutes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply domain-specific reasoning rules to refine statute list."""
    normalized_domain = (domain or "").strip().lower()
    base_statutes = [dict(item) for item in (statutes or [])]
    for item in base_statutes:
        item.setdefault("source", "retrieval")

    tax_statutes, tax_added = _apply_tax_rules(query, base_statutes)
    if tax_added:
        logger.info("reasoning_added_sections=%s", tax_added)
        return tax_statutes[:5]

    rules = {
        "family": _apply_family_rules,
        "criminal": _apply_criminal_rules,
    }

    rule_fn = rules.get(normalized_domain)
    if not rule_fn:
        return _dedupe_preserve(base_statutes)[:5]

    final_statutes, added_count = rule_fn(query, base_statutes)
    logger.info("reasoning_added_sections=%s", added_count)
    return final_statutes[:5]


def _apply_family_rules(
    query: str, statutes: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:
    query_lower = (query or "").lower()
    # Domestic violence / cruelty / dowry triggers
    domestic_triggers = (
        "domestic violence",
        "beating",
        "abuse",
        "cruelty",
        "dowry",
        "harass",
        "torture",
        "husband is beating",
        "wife is beating",
        "spousal abuse",
    )
    if any(trigger in query_lower for trigger in domestic_triggers):
        priority = [
            _statute("Bharatiya Nyaya Sanhita", 2023, "85", "Cruelty by husband or relatives"),
            _statute("Indian Penal Code", 1860, "498A", "Cruelty by husband or relatives"),
            _statute("Protection of Women from Domestic Violence Act", 2005, "3", "Definition of domestic violence"),
            _statute("Dowry Prohibition Act", 1961, "4", "Penalty for demanding dowry"),
        ]
        merged, added_count = _merge_with_priority(statutes, priority)
        return merged, added_count

    divorce_triggers = ("divorce", "separation", "marital dispute")
    if any(trigger in query_lower for trigger in divorce_triggers):
        priority = [
            _statute("Hindu Marriage Act", 1955, "13", "Divorce"),
            _statute("Hindu Marriage Act", 1955, "13B", "Divorce by mutual consent"),
            _statute("Hindu Marriage Act", 1955, "24", "Maintenance pendente lite"),
            _statute("Hindu Marriage Act", 1955, "25", "Permanent alimony and maintenance"),
        ]
        merged, added_count = _merge_with_priority(statutes, priority)
        return merged, added_count

    return _dedupe_preserve(statutes), 0


def _apply_criminal_rules(
    query: str, statutes: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:
    query_lower = (query or "").lower()
    suicide_triggers = (
        "suicide",
        "committed suicide",
        "done suicide",
        "killed himself",
        "killed herself",
        "took own life",
    )
    if any(trigger in query_lower for trigger in suicide_triggers):
        priority = [
            _statute("Bharatiya Nyaya Sanhita", 2023, "108", "Abetment of suicide"),
            _statute("Indian Penal Code", 1860, "306", "Abetment of suicide"),
            _statute("Indian Penal Code", 1860, "305", "Abetment of suicide of child or insane person"),
            _statute("Indian Penal Code", 1860, "309", "Attempt to commit suicide"),
        ]
        merged, added_count = _merge_with_priority(statutes, priority)
        merged = [
            statute for statute in merged
            if not (
                statute.get("act") == "Bharatiya Nyaya Sanhita"
                and str(statute.get("section", "")).strip() in {"305", "306", "309"}
            )
        ]
        return merged, added_count

    tax_triggers = (
        "tax",
        "gst",
        "income tax",
        "tax not paid",
        "non-payment of tax",
        "tax evasion",
        "tax default",
    )
    if any(trigger in query_lower for trigger in tax_triggers):
        priority = _tax_priority_statutes()
        merged, added_count = _merge_with_priority(statutes, priority)
        return merged, added_count

    child_sexual_triggers = (
        "pedophile",
        "paedophile",
        "child abuse",
        "minor sexual",
        "molested child",
        "sex with child",
        "raping child",
        "raping minor",
        "year old girl",
        "year old boy",
    )
    if not any(trigger in query_lower for trigger in child_sexual_triggers):
        return _dedupe_preserve(statutes), 0

    priority = [
        _statute("Protection of Children from Sexual Offences Act", 2012, "3", "Penetrative sexual assault"),
        _statute("Protection of Children from Sexual Offences Act", 2012, "4", "Punishment for penetrative sexual assault"),
        _statute("Protection of Children from Sexual Offences Act", 2012, "7", "Sexual assault"),
        _statute("Protection of Children from Sexual Offences Act", 2012, "8", "Punishment for sexual assault"),
        _statute("Bharatiya Nyaya Sanhita", 2023, "64", "Rape"),
        _statute("Bharatiya Nyaya Sanhita", 2023, "65", "Punishment for rape"),
        _statute("Indian Penal Code", 1860, "375", "Rape"),
        _statute("Indian Penal Code", 1860, "376", "Punishment for rape"),
    ]

    merged, added_count = _merge_with_priority(statutes, priority)
    merged = [
        statute for statute in merged
        if not (
            statute.get("act") == "Indian Penal Code"
            and str(statute.get("section", "")).strip() == "377"
        )
    ]
    return merged, added_count


def _apply_tax_rules(
    query: str, statutes: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:
    query_lower = (query or "").lower()
    tax_triggers = (
        "tax",
        "gst",
        "income tax",
        "tax not paid",
        "non-payment of tax",
        "tax evasion",
        "tax default",
    )
    if not any(trigger in query_lower for trigger in tax_triggers):
        return _dedupe_preserve(statutes), 0
    priority = _tax_priority_statutes()
    merged, added_count = _merge_with_priority(statutes, priority)
    return merged, added_count


def _tax_priority_statutes() -> List[Dict[str, Any]]:
    return [
        _statute("Income-tax Act", 1961, "276C", "Wilful attempt to evade tax, penalty or interest"),
        _statute("Income-tax Act", 1961, "270A", "Penalty for under-reporting and misreporting of income"),
        _statute("Income-tax Act", 1961, "271AAD", "Penalty for false entry or omitted entry in books of account"),
        _statute("Central Goods and Services Tax Act", 2017, "76", "Tax collected but not paid to Government"),
        _statute("Central Goods and Services Tax Act", 2017, "122", "Penalty for certain offences"),
        _statute("Central Goods and Services Tax Act", 2017, "132", "Punishment for certain offences"),
        _statute("Central Goods and Services Tax Act", 2017, "73", "Determination of tax not paid or short paid"),
        _statute("Central Goods and Services Tax Act", 2017, "74", "Determination of tax not paid or short paid (fraud)"),
    ]

def _merge_with_priority(
    statutes: List[Dict[str, Any]], priority: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:
    existing_map = {_statute_key(item): item for item in statutes}
    added_count = 0

    prioritized: List[Dict[str, Any]] = []
    for rule_statute in priority:
        key = _statute_key(rule_statute)
        if key in existing_map:
            prioritized.append(existing_map[key])
        else:
            added = dict(rule_statute)
            added["source"] = "reasoning_engine"
            prioritized.append(added)
            added_count += 1

    remaining: List[Dict[str, Any]] = []
    priority_keys = {_statute_key(item) for item in prioritized}
    for item in statutes:
        if _statute_key(item) in priority_keys:
            continue
        remaining.append(item)

    combined = prioritized + remaining
    return _dedupe_preserve(combined), added_count


def _statute(act: str, year: int, section: str, title: str) -> Dict[str, Any]:
    return {
        "act": act,
        "year": year,
        "section": section,
        "title": title,
    }


def _statute_key(item: Dict[str, Any]) -> str:
    return "|".join(
        [
            str(item.get("act", "")).strip().lower(),
            str(item.get("year", "")).strip(),
            str(item.get("section", "")).strip().lower(),
        ]
    )


def _dedupe_preserve(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    output: List[Dict[str, Any]] = []
    for item in items:
        key = _statute_key(item)
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output
