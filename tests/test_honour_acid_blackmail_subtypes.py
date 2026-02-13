import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.addons.addon_subtype_resolver import AddonSubtypeResolver

def test_honour_killing():
    resolver = AddonSubtypeResolver()
    
    query = "family killed girl for love marriage"
    subtype = resolver.detect_addon_subtype(query)
    
    print(f"Query: {query}")
    print(f"Detected subtype: {subtype}")
    
    assert subtype == "honour_killing", f"Expected honour_killing, got {subtype}"
    
    base_response = {"statutes": [], "domains": ["criminal"]}
    confidence = {"statute_match": 0.3}
    
    enhanced = resolver.enhance_response(base_response, query, confidence)
    
    assert len(enhanced["statutes"]) >= 1, "Expected at least 1 statute"
    assert any(s["section"] == "103" for s in enhanced["statutes"]), "Expected BNS 103 (Murder)"
    assert enhanced["enforcement_decision"] == "ESCALATE"
    assert "family" in enhanced["domains"]
    
    print("[PASS] Honour killing test passed")
    print(f"  Statutes: {[s['section'] for s in enhanced['statutes']]}")

def test_acid_attack():
    resolver = AddonSubtypeResolver()
    
    query = "someone threw acid on me"
    subtype = resolver.detect_addon_subtype(query)
    
    assert subtype == "acid_attack", f"Expected acid_attack, got {subtype}"
    
    base_response = {"statutes": [], "domains": ["criminal"]}
    confidence = {"statute_match": 0.2}
    
    enhanced = resolver.enhance_response(base_response, query, confidence)
    
    assert len(enhanced["statutes"]) >= 1, "Expected at least 1 statute"
    assert any(s["section"] == "124" for s in enhanced["statutes"]), "Expected BNS 124 (Grievous hurt by dangerous means)"
    assert enhanced["enforcement_decision"] == "ESCALATE"
    
    print("[PASS] Acid attack test passed")
    print(f"  Statutes: {[s['section'] for s in enhanced['statutes']]}")

def test_blackmail_extortion():
    resolver = AddonSubtypeResolver()
    
    query = "he is blackmailing me with photos"
    subtype = resolver.detect_addon_subtype(query)
    
    assert subtype == "blackmail_extortion", f"Expected blackmail_extortion, got {subtype}"
    
    base_response = {"statutes": [], "domains": ["criminal"]}
    confidence = {"statute_match": 0.4}
    
    enhanced = resolver.enhance_response(base_response, query, confidence)
    
    assert len(enhanced["statutes"]) >= 2, "Expected at least 2 statutes"
    assert any(s["section"] == "308" for s in enhanced["statutes"]), "Expected BNS 308 (Extortion)"
    assert any(s["section"] == "67" and s["act"] == "Information Technology Act" for s in enhanced["statutes"]), "Expected IT Act 67"
    assert enhanced["enforcement_decision"] == "ESCALATE"
    
    print("[PASS] Blackmail/extortion test passed")
    print(f"  Statutes: {[s['section'] for s in enhanced['statutes']]}")

if __name__ == "__main__":
    test_honour_killing()
    test_acid_attack()
    test_blackmail_extortion()
    print("\n[SUCCESS] All tests passed!")
