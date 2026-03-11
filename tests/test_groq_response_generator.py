from core.llm.groq_client import GroqResponseGenerator


def test_local_answer_without_groq_key():
    generator = GroqResponseGenerator()
    generator.enabled = True
    generator.api_key = ""

    result = generator.generate_answer(
        query="What is the punishment for theft in India?",
        jurisdiction="IN",
        domain="criminal",
        statutes=[
            {
                "act": "Indian Penal Code",
                "year": 1860,
                "section": "379",
                "title": "Punishment for theft",
            }
        ],
        case_laws=[],
        procedural_steps=["File FIR", "Investigation", "Trial"],
        remedies=["Criminal prosecution"],
        timeline=[{"step": "File FIR", "eta": "1 day"}],
        evidence_requirements=["Complaint copy", "Witness statements"],
        enforcement_decision="ALLOW",
        legal_analysis="Legal Analysis for IN Jurisdiction:",
    )

    assert result["source"] == "local"
    assert "Section 379 of Indian Penal Code (1860)" in result["text"]
    assert "Enforcement: ALLOW" in result["text"]


def test_local_fallback_when_remote_generation_fails():
    generator = GroqResponseGenerator()
    generator.enabled = True
    generator.api_key = "test-key"
    generator.base_url = "http://127.0.0.1:1"
    generator.timeout_seconds = 0.1

    result = generator.generate_answer(
        query="How do I file a theft complaint?",
        jurisdiction="IN",
        domain="criminal",
        statutes=[],
        case_laws=[],
        procedural_steps=["File FIR"],
        remedies=[],
        timeline=[],
        evidence_requirements=[],
        enforcement_decision="ALLOW",
        legal_analysis="Legal Analysis for IN Jurisdiction:",
    )

    assert result["source"] == "local_fallback"
    assert "How do I file a theft complaint?" in result["text"]
