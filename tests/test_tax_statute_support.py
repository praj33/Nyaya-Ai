import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from clean_legal_advisor import EnhancedLegalAdvisor, LegalQuery
from core.ontology.statute_resolver import StatuteResolver


def test_statute_resolver_returns_income_tax_sections():
    resolver = StatuteResolver(use_faiss=False)

    result = resolver.resolve_query("income tax evasion penalty", ["civil"], "IN")
    acts = {item["act"] for item in result["statutes"]}
    sections = {item["section"] for item in result["statutes"]}

    assert "Income-tax Act" in acts
    assert sections & {"270A", "276C", "276CC"}


def test_statute_resolver_returns_gst_sections():
    resolver = StatuteResolver(use_faiss=False)

    result = resolver.resolve_query("GST fake invoice penalty", ["civil"], "IN")
    acts = {item["act"] for item in result["statutes"]}
    sections = {item["section"] for item in result["statutes"]}

    assert "Central Goods and Services Tax Act" in acts
    assert sections & {"122", "132"}


def test_enhanced_advisor_prefers_tax_statutes_over_cpc():
    advisor = EnhancedLegalAdvisor()

    advice = advisor.provide_legal_advice(LegalQuery("GST fake invoice penalty", "India", None))
    acts = {item["act"] for item in advice.statutes}

    assert "Central Goods and Services Tax Act" in acts
    assert "Code of Civil Procedure" not in acts
