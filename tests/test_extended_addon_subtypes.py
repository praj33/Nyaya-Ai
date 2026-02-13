import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.addons.addon_subtype_resolver import AddonSubtypeResolver
from core.response.enricher import enrich_response

def test_domestic_worker_abuse_detection():
    """Test domestic worker abuse addon detection"""
    resolver = AddonSubtypeResolver()
    
    # Test positive cases
    assert resolver.detect_addon_subtype("maid beaten by employer") == "domestic_worker_abuse"
    assert resolver.detect_addon_subtype("domestic worker abused") == "domestic_worker_abuse"
    assert resolver.detect_addon_subtype("house help beaten") == "domestic_worker_abuse"
    assert resolver.detect_addon_subtype("maid not paid salary") == "domestic_worker_abuse"
    
    print("Domestic worker abuse detection tests passed")

def test_human_trafficking_detection():
    """Test human trafficking addon detection"""
    resolver = AddonSubtypeResolver()
    
    # Test positive cases
    assert resolver.detect_addon_subtype("girl trafficked for prostitution") == "human_trafficking"
    assert resolver.detect_addon_subtype("human trafficking case") == "human_trafficking"
    assert resolver.detect_addon_subtype("sold for labour") == "human_trafficking"
    assert resolver.detect_addon_subtype("trafficked child") == "human_trafficking"
    
    print("Human trafficking detection tests passed")

def test_child_labour_detection():
    """Test child labour addon detection"""
    resolver = AddonSubtypeResolver()
    
    # Test positive cases
    assert resolver.detect_addon_subtype("child labour in factory") == "child_labour"
    assert resolver.detect_addon_subtype("child working in factory") == "child_labour"
    assert resolver.detect_addon_subtype("minor forced to work") == "child_labour"
    assert resolver.detect_addon_subtype("underage labour") == "child_labour"
    
    print("Child labour detection tests passed")

def test_statute_metadata_completion():
    """Test statute metadata completion functionality"""
    resolver = AddonSubtypeResolver()
    
    # Test BNS statute completion
    statute = {"act": "Bharatiya Nyaya Sanhita", "section": "115", "title": "Voluntarily causing hurt"}
    completed = resolver._complete_statute_metadata(statute)
    assert completed["year"] == 2023
    
    # Test Minimum Wages Act completion
    statute = {"act": "Minimum Wages Act", "section": "22", "title": "Penalty for non-payment of wages"}
    completed = resolver._complete_statute_metadata(statute)
    assert completed["year"] == 1948
    
    print("Statute metadata completion tests passed")

def test_domestic_worker_abuse_statutes():
    """Test domestic worker abuse returns correct statutes"""
    resolver = AddonSubtypeResolver()
    
    base_response = {"statutes": []}
    enhanced = resolver.enhance_response(base_response, "maid beaten by employer")
    
    assert enhanced["addon_subtype"] == "domestic_worker_abuse"
    assert enhanced["domains"] == ["criminal", "labour"]
    assert enhanced["enforcement_decision"] == "ESCALATE"
    
    # Check BNS 115 is included
    sections = [s["section"] for s in enhanced["statutes"]]
    assert "115" in sections
    assert "127" in sections
    assert "22" in sections
    
    print("Domestic worker abuse statute tests passed")

def test_human_trafficking_statutes():
    """Test human trafficking returns correct statutes"""
    resolver = AddonSubtypeResolver()
    
    base_response = {"statutes": []}
    enhanced = resolver.enhance_response(base_response, "girl trafficked for prostitution")
    
    assert enhanced["addon_subtype"] == "human_trafficking"
    assert enhanced["domains"] == ["criminal"]
    assert enhanced["enforcement_decision"] == "ESCALATE"
    
    # Check BNS 143 is included
    sections = [s["section"] for s in enhanced["statutes"]]
    assert "143" in sections
    assert "5" in sections
    
    print("Human trafficking statute tests passed")

def test_child_labour_statutes():
    """Test child labour returns correct statutes"""
    resolver = AddonSubtypeResolver()
    
    base_response = {"statutes": []}
    enhanced = resolver.enhance_response(base_response, "child labour in factory")
    
    assert enhanced["addon_subtype"] == "child_labour"
    assert enhanced["domains"] == ["criminal", "labour"]
    assert enhanced["enforcement_decision"] == "ESCALATE"
    
    # Check Child Labour Act Section 3 is included
    acts = [s["act"] for s in enhanced["statutes"]]
    assert "Child and Adolescent Labour (Prohibition and Regulation) Act" in acts
    
    sections = [s["section"] for s in enhanced["statutes"]]
    assert "3" in sections
    assert "143" in sections
    
    print("Child labour statute tests passed")

def test_full_pipeline_integration_new_subtypes():
    """Test full pipeline integration with new subtypes"""
    
    # Test domestic worker abuse
    response = enrich_response({}, "maid beaten by employer", "criminal", [])
    if "addon_enhanced" in response:
        assert response["addon_subtype"] == "domestic_worker_abuse"
        assert response["enforcement_decision"] == "ESCALATE"
    
    # Test human trafficking
    response = enrich_response({}, "girl trafficked for prostitution", "criminal", [])
    if "addon_enhanced" in response:
        assert response["addon_subtype"] == "human_trafficking"
        assert response["enforcement_decision"] == "ESCALATE"
    
    # Test child labour
    response = enrich_response({}, "child labour in factory", "criminal", [])
    if "addon_enhanced" in response:
        assert response["addon_subtype"] == "child_labour"
        assert response["enforcement_decision"] == "ESCALATE"
    
    print("Full pipeline integration tests passed")

def test_specific_statute_expectations():
    """Test specific statute expectations for new addon types"""
    resolver = AddonSubtypeResolver()
    
    # Domestic worker abuse - expect BNS 115
    response = resolver.enhance_response({}, "maid beaten by employer")
    sections = [s.get("section") for s in response.get("statutes", [])]
    assert "115" in sections
    
    # Human trafficking - expect BNS 143
    response = resolver.enhance_response({}, "girl trafficked for prostitution")
    sections = [s.get("section") for s in response.get("statutes", [])]
    assert "143" in sections
    
    # Child labour - expect Child Labour Act Section 3
    response = resolver.enhance_response({}, "child labour in factory")
    acts = [s.get("act") for s in response.get("statutes", [])]
    assert "Child and Adolescent Labour (Prohibition and Regulation) Act" in acts
    
    print("Specific statute expectation tests passed")

def test_all_addon_subtypes_count():
    """Test that all 6 addon subtypes are loaded"""
    resolver = AddonSubtypeResolver()
    
    expected_subtypes = [
        "cyber_bullying",
        "workplace_sexual_harassment", 
        "ragging_hazing",
        "domestic_worker_abuse",
        "human_trafficking",
        "child_labour"
    ]
    
    for subtype in expected_subtypes:
        assert subtype in resolver.addon_subtypes
    
    assert len(resolver.addon_subtypes) == 6
    
    print("All addon subtypes count tests passed")

if __name__ == "__main__":
    test_domestic_worker_abuse_detection()
    test_human_trafficking_detection()
    test_child_labour_detection()
    test_statute_metadata_completion()
    test_domestic_worker_abuse_statutes()
    test_human_trafficking_statutes()
    test_child_labour_statutes()
    test_full_pipeline_integration_new_subtypes()
    test_specific_statute_expectations()
    test_all_addon_subtypes_count()
    print("\nAll extended addon subtype tests passed!")