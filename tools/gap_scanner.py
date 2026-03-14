"""Gap scanner for issue profiles vs DB statutes."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from data_bridge.loader import JSONLoader

logger = logging.getLogger(__name__)


def scan_gaps(output_path: Path | None = None) -> Dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[2]
    db_path = repo_root / "Nyaya_AI" / "db"
    ontology_path = repo_root / "Nyaya_AI" / "core" / "ontology" / "indian_legal_ontology.json"

    profiles = _load_issue_profiles(repo_root)
    act_name_to_id = _load_act_name_map(ontology_path)
    sections_by_act = _load_sections_by_act(db_path)

    missing_sections: List[Dict[str, Any]] = []
    unmapped_acts: List[Dict[str, Any]] = []
    missing_act_data: List[Dict[str, Any]] = []

    for profile in profiles:
        profile_name = profile["name"]
        source = profile["source"]
        data = profile["data"]
        for statute in data.get("statutes", []):
            act_name = str(statute.get("act", "")).strip()
            section = str(statute.get("section", "")).strip()
            if not act_name or not section:
                continue
            act_id = act_name_to_id.get(act_name.lower())
            if not act_id:
                unmapped_acts.append(
                    {
                        "issue_profile": profile_name,
                        "source": source,
                        "act": act_name,
                        "section": section,
                    }
                )
                continue
            available_sections = sections_by_act.get(act_id)
            if not available_sections:
                missing_act_data.append(
                    {
                        "issue_profile": profile_name,
                        "source": source,
                        "act": act_name,
                        "act_id": act_id,
                        "section": section,
                    }
                )
                continue
            if section.lower() not in available_sections:
                missing_sections.append(
                    {
                        "issue_profile": profile_name,
                        "source": source,
                        "act": act_name,
                        "act_id": act_id,
                        "section": section,
                    }
                )

    report = {
        "summary": {
            "profiles_scanned": len(profiles),
            "missing_sections": len(missing_sections),
            "unmapped_acts": len(unmapped_acts),
            "missing_act_data": len(missing_act_data),
        },
        "missing_sections": missing_sections,
        "unmapped_acts": unmapped_acts,
        "missing_act_data": missing_act_data,
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info("Gap report written to %s", output_path)

    return report


def _load_issue_profiles(repo_root: Path) -> List[Dict[str, Any]]:
    profiles: List[Dict[str, Any]] = []
    sources = [
        repo_root / "Nyaya_AI" / "core" / "ontology" / "offense_subtypes.json",
        repo_root / "Nyaya_AI" / "core" / "addons" / "offense_subtypes_addon.json",
        repo_root / "Nyaya_AI" / "core" / "addons" / "offense_subtypes_addon_multi_jurisdiction.json",
    ]
    for path in sources:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            continue
        for name, payload in data.items():
            profiles.append({"name": name, "data": payload, "source": str(path)})
    return profiles


def _load_act_name_map(ontology_path: Path) -> Dict[str, str]:
    if not ontology_path.exists():
        return {}
    with ontology_path.open("r", encoding="utf-8") as f:
        ontology = json.load(f)
    act_map = {}
    for act in ontology.get("acts", []):
        name = str(act.get("name", "")).strip()
        act_id = str(act.get("act_id", "")).strip()
        if name and act_id:
            act_map[name.lower()] = act_id
    return act_map


def _load_sections_by_act(db_path: Path) -> Dict[str, set]:
    if not db_path.exists():
        return {}
    loader = JSONLoader(str(db_path))
    sections, _acts, _cases = loader.load_and_normalize_directory(str(db_path))
    sections_by_act: Dict[str, set] = {}
    for section in sections:
        act_id = _normalize_act_id(section.act_id)
        if not act_id:
            continue
        sections_by_act.setdefault(act_id, set()).add(str(section.section_number).strip().lower())
    return sections_by_act


def _normalize_act_id(act_id: str) -> str:
    if not act_id:
        return ""
    value = act_id.lower().strip()
    if value.startswith("in_"):
        value = value[3:]
    if value.startswith("uk_"):
        value = value[3:]
    if value.startswith("uae_"):
        value = value[4:]
    return value


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output_path = repo_root / "data" / "gap_report.json"
    report = scan_gaps(output_path)
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
