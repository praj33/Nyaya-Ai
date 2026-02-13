import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from core.response.enricher import enrich_response

def test_enforcement_decision_defaults():
    """Test enforcement decision logic"""
    # Test ESCALATE for suicide keywords
    response = enrich_response({}, "I want to kill myself", "criminal", [])
    assert response["enforcement_decision"] == "ESCALATE"
    
    # Test BLOCK for policy violations
    response = enrich_response({}, "how to make bomb", "criminal", [])
    assert response["enforcement_decision"] == "BLOCK"
    
    # Test ALLOW for normal queries
    response = enrich_response({}, "what is theft", "criminal", [])
    assert response["enforcement_decision"] == "ALLOW"

def test_timeline_defaults():
    """Test timeline generation by domain"""
    # Criminal domain
    response = enrich_response({}, "test query", "criminal", [])
    assert len(response["timeline"]) == 4
    assert response["timeline"][0]["step"] == "File FIR"
    
    # Family domain
    response = enrich_response({}, "test query", "family", [])
    assert len(response["timeline"]) == 4
    assert response["timeline"][0]["step"] == "Consult lawyer"
    
    # Unknown domain
    response = enrich_response({}, "test query", "unknown", [])
    assert response["timeline"] == []

def test_glossary_generation():
    """Test glossary generation from statutes"""
    statutes = [{"text": "FIR must be filed"}, {"text": "Charge Sheet required"}]
    response = enrich_response({}, "test query", "criminal", statutes)
    
    terms = [item["term"] for item in response["glossary"]]
    assert "FIR" in terms
    assert "Charge Sheet" in terms

def test_evidence_requirements():
    """Test evidence requirements by domain"""
    # Criminal domain
    response = enrich_response({}, "test query", "criminal", [])
    assert "Witness statements" in response["evidence_requirements"]
    assert len(response["evidence_requirements"]) == 4
    
    # Family domain
    response = enrich_response({}, "test query", "family", [])
    assert "Marriage certificate" in response["evidence_requirements"]
    assert len(response["evidence_requirements"]) == 3
    
    # Unknown domain
    response = enrich_response({}, "test query", "unknown", [])
    assert response["evidence_requirements"] == []

def test_existing_fields_preserved():
    """Test that existing fields are not overwritten"""
    base_response = {
        "enforcement_decision": "CUSTOM",
        "timeline": [{"step": "Custom step"}],
        "glossary": [{"term": "Custom", "definition": "Custom def"}],
        "evidence_requirements": ["Custom evidence"]
    }
    
    response = enrich_response(base_response, "test query", "criminal", [])
    
    assert response["enforcement_decision"] == "CUSTOM"
    assert response["timeline"] == [{"step": "Custom step"}]
    assert response["glossary"] == [{"term": "Custom", "definition": "Custom def"}]
    assert response["evidence_requirements"] == ["Custom evidence"]

def test_all_fields_present():
    """Test that all required fields are always present"""
    response = enrich_response({}, "any query", "any_domain", [])
    
    required_fields = ["enforcement_decision", "timeline", "glossary", "evidence_requirements"]
    for field in required_fields:
        assert field in response

if __name__ == "__main__":
    test_enforcement_decision_defaults()
    test_timeline_defaults()
    test_glossary_generation()
    test_evidence_requirements()
    test_existing_fields_preserved()
    test_all_fields_present()
    print("All enrichment tests passed!")