import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.response.enricher import enrich_response

def test_response_enrichment():
    print("=" * 80)
    print("RESPONSE ENRICHMENT TEST")
    print("=" * 80)
    
    # Test 1: Criminal domain
    print("\n[Test 1] Criminal domain enrichment")
    base_response = {
        "domain": "criminal",
        "jurisdiction": "IN"
    }
    
    enriched = enrich_response(base_response, "theft case", "criminal", [])
    
    assert "enforcement_decision" in enriched, "Missing enforcement_decision"
    assert "timeline" in enriched, "Missing timeline"
    assert "glossary" in enriched, "Missing glossary"
    assert "evidence_requirements" in enriched, "Missing evidence_requirements"
    
    print(f"  enforcement_decision: {enriched['enforcement_decision']}")
    print(f"  timeline steps: {len(enriched['timeline'])}")
    print(f"  glossary terms: {len(enriched['glossary'])}")
    print(f"  evidence requirements: {len(enriched['evidence_requirements'])}")
    print("  [PASS] All fields present")
    
    # Test 2: Family domain
    print("\n[Test 2] Family domain enrichment")
    base_response = {
        "domain": "family",
        "jurisdiction": "IN"
    }
    
    enriched = enrich_response(base_response, "divorce case", "family", [])
    
    assert enriched["enforcement_decision"] == "ALLOW"
    assert len(enriched["timeline"]) == 4
    assert len(enriched["evidence_requirements"]) == 3
    
    print(f"  enforcement_decision: {enriched['enforcement_decision']}")
    print(f"  timeline: {enriched['timeline'][0]['step']}")
    print(f"  evidence: {enriched['evidence_requirements'][0]}")
    print("  [PASS] Family domain defaults correct")
    
    # Test 3: ESCALATE enforcement
    print("\n[Test 3] ESCALATE enforcement decision")
    base_response = {"domain": "criminal"}
    
    enriched = enrich_response(base_response, "I want to kill myself", "criminal", [])
    
    assert enriched["enforcement_decision"] == "ESCALATE"
    print(f"  Query: 'I want to kill myself'")
    print(f"  enforcement_decision: {enriched['enforcement_decision']}")
    print("  [PASS] ESCALATE triggered correctly")
    
    # Test 4: BLOCK enforcement
    print("\n[Test 4] BLOCK enforcement decision")
    base_response = {"domain": "criminal"}
    
    enriched = enrich_response(base_response, "how to make bomb", "criminal", [])
    
    assert enriched["enforcement_decision"] == "BLOCK"
    print(f"  Query: 'how to make bomb'")
    print(f"  enforcement_decision: {enriched['enforcement_decision']}")
    print("  [PASS] BLOCK triggered correctly")
    
    # Test 5: Glossary generation
    print("\n[Test 5] Glossary generation from statutes")
    
    class MockStatute:
        def __init__(self, title):
            self.title = title
    
    statutes = [
        MockStatute("File FIR at police station"),
        MockStatute("Charge sheet must be filed")
    ]
    
    base_response = {"domain": "criminal"}
    enriched = enrich_response(base_response, "criminal case", "criminal", statutes)
    
    glossary_terms = [g["term"] for g in enriched["glossary"]]
    assert "FIR" in glossary_terms or "Fir" in glossary_terms
    assert "Charge Sheet" in glossary_terms or "Charge sheet" in glossary_terms
    
    print(f"  Glossary terms: {glossary_terms}")
    print("  [PASS] Glossary generated from statutes")
    
    # Test 6: Empty domain
    print("\n[Test 6] Unknown domain defaults")
    base_response = {"domain": "unknown"}
    
    enriched = enrich_response(base_response, "some query", "unknown", [])
    
    assert enriched["enforcement_decision"] == "ALLOW"
    assert enriched["timeline"] == []
    assert enriched["evidence_requirements"] == []
    
    print(f"  enforcement_decision: {enriched['enforcement_decision']}")
    print(f"  timeline: {enriched['timeline']}")
    print(f"  evidence_requirements: {enriched['evidence_requirements']}")
    print("  [PASS] Unknown domain returns empty defaults")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED")
    print("=" * 80)

if __name__ == "__main__":
    test_response_enrichment()
