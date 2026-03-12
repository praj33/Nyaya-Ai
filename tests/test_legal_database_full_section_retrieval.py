import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from legal_database.database_loader import legal_db


def test_companies_act_sections_are_retrieved_from_full_corpus():
    sections = legal_db.get_legal_sections(
        "private company minimum directors",
        "India",
        "civil",
        limit=5,
    )

    assert sections
    assert any(item["act"] == "Companies Act, 2013" and item["section"] == "149" for item in sections)


def test_arbitration_act_sections_are_retrieved_from_full_corpus():
    sections = legal_db.get_legal_sections(
        "arbitral award setting aside",
        "India",
        "civil",
        limit=5,
    )

    assert sections
    assert any(
        item["act"] == "Arbitration and Conciliation Act, 1996" and item["section"] == "34"
        for item in sections
    )


def test_section_number_queries_use_exact_section_boost():
    sections = legal_db.get_legal_sections(
        "section 149 directors",
        "India",
        "civil",
        limit=5,
    )

    assert sections
    assert sections[0]["section"] == "149"
    assert sections[0]["act"] == "Companies Act, 2013"
