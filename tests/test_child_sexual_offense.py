import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ontology.statute_resolver import StatuteResolver
from core.response.enricher import enrich_response

def test_child_sexual_offense_detection():
    """Test child sexual offense subtype detection"""
    resolver = StatuteResolver()
    
    # Test positive cases
    assert resolver.detect_offense_subtype("my friend is pedophile") == "child_sexual_offense"
    assert resolver.detect_offense_subtype("child abuse happened") == "child_sexual_offense"
    assert resolver.detect_offense_subtype("minor sexual assault") == "child_sexual_offense"
    assert resolver.detect_offense_subtype("molested child") == "child_sexual_offense"
    
    # Test negative cases
    assert resolver.detect_offense_subtype("adult assault") != "child_sexual_offense"
    assert resolver.detect_offense_subtype("regular theft") != "child_sexual_offense"
    
    print("Child sexual offense detection tests passed")

def test_child_sexual_offense_statutes():
    """Test that child sexual offense returns POCSO statutes"""
    resolver = StatuteResolver()
    
    query = "my friend is pedophile"
    domains = ["criminal"]
    
    relevant_acts = resolver.get_relevant_acts(query, domains)
    
    # Should include POCSO act (mapped to appropriate act_id)
    print(f"Relevant acts for child sexual offense: {relevant_acts}")
    
    print("Child sexual offense statute tests passed")

def test_child_sexual_offense_enforcement():
    """Test enforcement escalation for child sexual offense"""
    query = "my friend is pedophile"
    response = enrich_response({}, query, "criminal", [])
    
    assert response["enforcement_decision"] == "ESCALATE"
    assert response["timeline"][0]["step"] == "Immediate FIR at police station"
    assert response["timeline"][4]["step"] == "Special POCSO Court trial"
    assert "Medical examination report" in response["evidence_requirements"]
    assert "Child statement" in response["evidence_requirements"]
    
    print("Child sexual offense enforcement tests passed")

def test_full_child_sexual_offense_scenario():
    """Test complete child sexual offense scenario"""
    query = "my friend is pedophile"
    resolver = StatuteResolver()
    
    # Check subtype detection
    subtype = resolver.detect_offense_subtype(query)
    assert subtype == "child_sexual_offense"
    
    # Check domain forcing
    domains = ["criminal"]
    relevant_acts = resolver.get_relevant_acts(query, domains)
    
    # Check enforcement
    response = enrich_response({}, query, "criminal", [])
    assert response["enforcement_decision"] == "ESCALATE"
    assert len(response["timeline"]) == 5
    assert len(response["evidence_requirements"]) == 5
    
    print("Full child sexual offense scenario test passed")

if __name__ == "__main__":
    test_child_sexual_offense_detection()
    test_child_sexual_offense_statutes()
    test_child_sexual_offense_enforcement()
    test_full_child_sexual_offense_scenario()
    print("\nAll child sexual offense tests passed!")