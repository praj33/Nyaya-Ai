#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.addons.addon_subtype_resolver import AddonSubtypeResolver

def test_honour_killing_detection():
    """Test honour killing detection"""
    resolver = AddonSubtypeResolver()
    
    # Test detection
    subtype = resolver.detect_addon_subtype("honour killing")
    print(f"Detected subtype: {subtype}")
    assert subtype == "honour_killing"
    
    # Test enhancement
    base_response = {"statutes": [], "domains": ["criminal"]}
    enhanced = resolver.enhance_response(base_response, "honour killing")
    
    assert enhanced["addon_enhanced"] == True
    assert enhanced["addon_subtype"] == "honour_killing"
    assert enhanced["enforcement_decision"] == "ESCALATE"
    assert any("103" in str(s) for s in enhanced["statutes"])
    
    print("Honour killing detection tests passed")

def test_acid_attack_detection():
    """Test acid attack detection"""
    resolver = AddonSubtypeResolver()
    
    # Test detection
    subtype = resolver.detect_addon_subtype("threw acid")
    print(f"Detected subtype: {subtype}")
    assert subtype == "acid_attack"
    
    # Test enhancement
    base_response = {"statutes": [], "domains": ["criminal"]}
    enhanced = resolver.enhance_response(base_response, "threw acid")
    
    assert enhanced["addon_enhanced"] == True
    assert enhanced["addon_subtype"] == "acid_attack"
    assert enhanced["enforcement_decision"] == "ESCALATE"
    assert any("124" in str(s) for s in enhanced["statutes"])
    
    print("Acid attack detection tests passed")

def test_blackmail_extortion_detection():
    """Test blackmail/extortion detection"""
    resolver = AddonSubtypeResolver()
    
    # Test detection
    subtype = resolver.detect_addon_subtype("blackmail")
    print(f"Detected subtype: {subtype}")
    assert subtype == "blackmail_extortion"
    
    # Test enhancement
    base_response = {"statutes": [], "domains": ["criminal"]}
    enhanced = resolver.enhance_response(base_response, "blackmail")
    
    assert enhanced["addon_enhanced"] == True
    assert enhanced["addon_subtype"] == "blackmail_extortion"
    assert enhanced["enforcement_decision"] == "ESCALATE"
    assert any("308" in str(s) for s in enhanced["statutes"])
    assert any("67" in str(s) for s in enhanced["statutes"])
    
    print("Blackmail/extortion detection tests passed")

def test_statute_completeness():
    """Test statute metadata completion for new subtypes"""
    resolver = AddonSubtypeResolver()
    
    # Test honour killing statutes have complete metadata
    base_response = {"statutes": [], "domains": ["criminal"]}
    enhanced = resolver.enhance_response(base_response, "honour killing")
    
    for statute in enhanced["statutes"]:
        assert "year" in statute
        assert statute["year"] is not None
        assert "title" in statute
        assert "act" in statute
        assert "section" in statute
    
    print("Statute completeness tests passed")

if __name__ == "__main__":
    test_honour_killing_detection()
    test_acid_attack_detection()
    test_blackmail_extortion_detection()
    test_statute_completeness()
    print("All new addon subtype tests passed!")