#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.addons.addon_subtype_resolver import AddonSubtypeResolver

def test_elder_abuse_detection():
    """Test elder abuse detection"""
    resolver = AddonSubtypeResolver()
    
    # Test detection
    subtype = resolver.detect_addon_subtype("old parents beaten")
    print(f"Detected subtype: {subtype}")
    assert subtype == "elder_abuse"
    
    # Test enhancement
    base_response = {"statutes": [], "domains": ["criminal"]}
    enhanced = resolver.enhance_response(base_response, "old parents beaten")
    
    assert enhanced["addon_enhanced"] == True
    assert enhanced["addon_subtype"] == "elder_abuse"
    assert enhanced["enforcement_decision"] == "ESCALATE"
    assert any("Senior Citizens Act" in str(s) for s in enhanced["statutes"])
    assert any("24" in str(s) for s in enhanced["statutes"])
    
    print("Elder abuse detection tests passed")

def test_organ_trafficking_detection():
    """Test organ trafficking detection"""
    resolver = AddonSubtypeResolver()
    
    # Test detection
    subtype = resolver.detect_addon_subtype("kidney selling racket caught")
    assert subtype == "organ_trafficking"
    
    # Test enhancement
    base_response = {"statutes": [], "domains": ["criminal"]}
    enhanced = resolver.enhance_response(base_response, "kidney selling racket caught")
    
    assert enhanced["addon_enhanced"] == True
    assert enhanced["addon_subtype"] == "organ_trafficking"
    assert enhanced["enforcement_decision"] == "ESCALATE"
    assert any("Transplantation of Human Organs" in str(s) for s in enhanced["statutes"])
    assert any("19" in str(s) for s in enhanced["statutes"])
    
    print("Organ trafficking detection tests passed")

def test_forced_marriage_detection():
    """Test forced marriage detection"""
    resolver = AddonSubtypeResolver()
    
    # Test detection
    subtype = resolver.detect_addon_subtype("parents forcing marriage")
    print(f"Detected subtype: {subtype}")
    assert subtype == "forced_marriage"
    
    # Test enhancement
    base_response = {"statutes": [], "domains": ["criminal"]}
    enhanced = resolver.enhance_response(base_response, "parents forcing marriage")
    
    assert enhanced["addon_enhanced"] == True
    assert enhanced["addon_subtype"] == "forced_marriage"
    assert enhanced["enforcement_decision"] == "ESCALATE"
    assert any("143" in str(s) for s in enhanced["statutes"])
    
    print("Forced marriage detection tests passed")

def test_statute_completeness():
    """Test statute metadata completion"""
    resolver = AddonSubtypeResolver()
    
    # Test elder abuse statutes have complete metadata
    base_response = {"statutes": [], "domains": ["criminal"]}
    enhanced = resolver.enhance_response(base_response, "old parents beaten")
    
    for statute in enhanced["statutes"]:
        assert "year" in statute
        assert statute["year"] is not None
        assert "title" in statute
        assert "act" in statute
        assert "section" in statute
    
    print("Statute completeness tests passed")

if __name__ == "__main__":
    test_elder_abuse_detection()
    test_organ_trafficking_detection()
    test_forced_marriage_detection()
    test_statute_completeness()
    print("All new addon subtype tests passed!")