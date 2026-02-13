import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ontology.statute_resolver import StatuteResolver
from core.response.enricher import enrich_response

def test_authority_assault_detection():
    """Test authority assault subtype detection"""
    resolver = StatuteResolver()
    
    # Test positive cases
    assert resolver.detect_offense_subtype("my teacher is beating me") == "authority_assault"
    assert resolver.detect_offense_subtype("coach hit me") == "authority_assault"
    assert resolver.detect_offense_subtype("principal slapped me") == "authority_assault"
    assert resolver.detect_offense_subtype("employer assaulted me") == "authority_assault"
    
    # Test negative cases (missing authority or violence)
    assert resolver.detect_offense_subtype("teacher gave homework") is None
    assert resolver.detect_offense_subtype("someone beat me") != "authority_assault"
    
    print("Authority assault detection tests passed")

def test_authority_assault_statutes():
    """Test that authority assault returns correct statutes"""
    resolver = StatuteResolver()
    
    query = "my teacher is beating me"
    domains = ["criminal"]
    
    relevant_acts = resolver.get_relevant_acts(query, domains)
    
    # Should include BNS sections
    assert "bns_sections" in relevant_acts
    print(f"Relevant acts for authority assault: {relevant_acts}")
    
    print("Authority assault statute tests passed")

def test_authority_assault_enforcement():
    """Test enforcement escalation for authority assault"""
    query = "my teacher is beating me"
    response = enrich_response({}, query, "criminal", [])
    
    assert response["enforcement_decision"] == "ESCALATE"
    assert response["timeline"][0]["step"] == "File FIR"
    assert len(response["evidence_requirements"]) == 4
    
    print("Authority assault enforcement tests passed")

def test_full_authority_assault_scenario():
    """Test complete authority assault scenario"""
    query = "my teacher is beating me"
    resolver = StatuteResolver()
    
    # Check subtype detection
    subtype = resolver.detect_offense_subtype(query)
    assert subtype == "authority_assault"
    
    # Check domain forcing
    domains = ["criminal"]
    relevant_acts = resolver.get_relevant_acts(query, domains)
    assert "bns_sections" in relevant_acts
    
    # Check enforcement
    response = enrich_response({}, query, "criminal", [])
    assert response["enforcement_decision"] == "ESCALATE"
    
    print("Full authority assault scenario test passed")

if __name__ == "__main__":
    test_authority_assault_detection()
    test_authority_assault_statutes()
    test_authority_assault_enforcement()
    test_full_authority_assault_scenario()
    print("\nAll authority assault tests passed!")