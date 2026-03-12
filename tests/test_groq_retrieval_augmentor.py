import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from core.llm.groq_retrieval import GroqRetrievalAugmentor
from data_bridge.schemas.section import Jurisdiction, Section


def test_local_query_understanding_extracts_hints():
    augmentor = GroqRetrievalAugmentor()
    augmentor.enabled = True
    augmentor.api_key = ""

    result = augmentor.understand_query(
        query="What is the punishment under section 379 IPC for theft in India?",
        jurisdiction_hint="India",
        domain_hint="criminal",
    )

    assert result["source"] == "local"
    assert "379" in result["section_hints"]
    assert "ipc_sections" in result["act_hints"]
    assert result["suggested_jurisdiction"] == "IN"


def test_local_rerank_prefers_section_hint_matches():
    augmentor = GroqRetrievalAugmentor()
    sections = [
        Section(
            section_id="s1",
            section_number="511",
            text="Attempting to commit offences punishable with imprisonment.",
            act_id="ipc_sections",
            jurisdiction=Jurisdiction.IN,
        ),
        Section(
            section_id="s2",
            section_number="379",
            text="Punishment for theft.",
            act_id="ipc_sections",
            jurisdiction=Jurisdiction.IN,
        ),
    ]

    result = augmentor.rerank_sections(
        query="What is punishment for section 379 IPC theft?",
        sections=sections,
        jurisdiction="IN",
        domain="criminal",
        understanding={
            "section_hints": ["379"],
            "act_hints": ["ipc_sections"],
            "keywords": ["theft", "punishment"],
        },
        top_k=2,
    )

    assert result["sections"][0].section_number == "379"


def test_local_query_understanding_extracts_tax_act_hints():
    augmentor = GroqRetrievalAugmentor()
    augmentor.enabled = True
    augmentor.api_key = ""

    result = augmentor.understand_query(
        query="What is the penalty for GST fake invoice and wrongful ITC in India?",
        jurisdiction_hint="India",
        domain_hint=None,
    )

    assert result["source"] == "local"
    assert "cgst_act_2017" in result["act_hints"]
    assert result["suggested_jurisdiction"] == "IN"
    assert result["suggested_domain"] == "civil"
