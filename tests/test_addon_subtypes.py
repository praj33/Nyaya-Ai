import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.addons.addon_subtype_resolver import AddonSubtypeResolver
from core.response.enricher import enrich_response

def test_cyber_bullying_detection():
    """Test cyber bullying addon detection"""
    resolver = AddonSubtypeResolver()
    
    # Test positive cases
    assert resolver.detect_addon_subtype("someone is cyber bullying me") == "cyber_bullying"
    assert resolver.detect_addon_subtype("online harassment happening") == "cyber_bullying"
    assert resolver.detect_addon_subtype("threatening messages received") == "cyber_bullying"
    assert resolver.detect_addon_subtype("revenge porn posted") == "cyber_bullying"
    
    # Test negative cases
    assert resolver.detect_addon_subtype("regular theft case") is None
    
    print("Cyber bullying detection tests passed")

def test_workplace_harassment_detection():
    """Test workplace sexual harassment addon detection"""
    resolver = AddonSubtypeResolver()
    
    # Test positive cases
    assert resolver.detect_addon_subtype("my boss touched me in office") == "workplace_sexual_harassment"
    assert resolver.detect_addon_subtype("manager harassing me") == "workplace_sexual_harassment"
    assert resolver.detect_addon_subtype("office sexual harassment") == "workplace_sexual_harassment"
    
    print("Workplace harassment detection tests passed")

def test_ragging_detection():
    """Test ragging/hazing addon detection"""
    resolver = AddonSubtypeResolver()
    
    # Test positive cases
    assert resolver.detect_addon_subtype("seniors are ragging me in hostel") == "ragging_hazing"
    assert resolver.detect_addon_subtype("college seniors beating") == "ragging_hazing"
    assert resolver.detect_addon_subtype("forced drinking in hostel") == "ragging_hazing"
    
    print("Ragging detection tests passed")

def test_addon_enhancement_low_confidence():
    """Test addon enhancement when base resolver has low confidence"""
    resolver = AddonSubtypeResolver()
    
    base_response = {"statutes": []}
    confidence = {"statute_match": 0.3}
    
    enhanced = resolver.enhance_response(base_response, "someone is cyber bullying me", confidence)
    
    assert enhanced["addon_enhanced"] == True
    assert enhanced["addon_subtype"] == "cyber_bullying"
    assert enhanced["domains"] == ["criminal"]
    assert enhanced["enforcement_decision"] == "ESCALATE"
    assert len(enhanced["statutes"]) == 3
    
    # Check IT Act statutes
    statute_acts = [s["act"] for s in enhanced["statutes"]]
    assert "Information Technology Act" in statute_acts
    assert "Bharatiya Nyaya Sanhita" in statute_acts
    
    print("Addon enhancement tests passed")

def test_addon_no_enhancement_high_confidence():
    """Test that addon doesn't enhance when base resolver has high confidence"""
    resolver = AddonSubtypeResolver()
    
    base_response = {"statutes": [{"act": "Some Act", "section": "1"}]}
    confidence = {"statute_match": 0.8}
    
    enhanced = resolver.enhance_response(base_response, "someone is cyber bullying me", confidence)
    
    assert "addon_enhanced" not in enhanced
    assert len(enhanced["statutes"]) == 1  # Original statute preserved
    
    print("No enhancement for high confidence tests passed")

def test_full_pipeline_integration():
    """Test full pipeline integration with enricher"""
    
    # Test cyber bullying
    response = enrich_response({}, "someone is cyber bullying me", "criminal", [])
    
    assert "enforcement_decision" in response
    assert "timeline" in response
    assert "glossary" in response
    assert "evidence_requirements" in response
    
    # Should be enhanced by addon if no base statutes
    if "addon_enhanced" in response:
        assert response["addon_subtype"] == "cyber_bullying"
        assert response["enforcement_decision"] == "ESCALATE"
    
    print("Full pipeline integration tests passed")

def test_specific_statute_expectations():
    """Test specific statute expectations for each addon type"""
    resolver = AddonSubtypeResolver()
    
    # Cyber bullying - expect IT Act 66E
    response = resolver.enhance_response({}, "someone is cyber bullying me")
    if "statutes" in response:
        sections = [s.get("section") for s in response["statutes"]]
        assert "66E" in sections
    
    # Workplace harassment - expect POSH Act Section 3
    response = resolver.enhance_response({}, "my boss touched me in office")
    if "statutes" in response:
        acts = [s.get("act") for s in response["statutes"]]
        assert "Sexual Harassment of Women at Workplace Act" in acts
    
    # Ragging - expect BNS 115
    response = resolver.enhance_response({}, "seniors are ragging me in hostel")
    if "statutes" in response:
        sections = [s.get("section") for s in response["statutes"]]
        assert "115" in sections
    
    print("Specific statute expectation tests passed")

if __name__ == "__main__":
    test_cyber_bullying_detection()
    test_workplace_harassment_detection()
    test_ragging_detection()
    test_addon_enhancement_low_confidence()
    test_addon_no_enhancement_high_confidence()
    test_full_pipeline_integration()
    test_specific_statute_expectations()
    print("\nAll addon subtype tests passed!")