"""
Test suite for Jurisdiction Detector
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.jurisdiction.detector import JurisdictionDetector


def test_indian_jurisdiction_detection():
    """Test detection of Indian jurisdiction from various queries"""
    detector = JurisdictionDetector()
    
    test_cases = [
        # Strong Indian indicators
        ("I want to file an FIR for theft", "IN", 0.8),
        ("What is Section 498A IPC?", "IN", 0.9),
        ("Can I get anticipatory bail in Mumbai?", "IN", 0.8),
        ("Dowry harassment case under BNS", "IN", 0.9),
        ("UAPA terrorism charges", "IN", 0.9),
        
        # Geographic indicators
        ("Property dispute in Delhi", "IN", 0.6),
        ("Marriage registration in Bangalore", "IN", 0.6),
        
        # Legal terms
        ("How to file chargesheet?", "IN", 0.8),
        ("Cognizable offense procedure", "IN", 0.8),
        ("High Court appeal process", "IN", 0.6),
        
        # Currency indicators
        ("Fraud of 10 lakh rupees", "IN", 0.7),
        ("Compensation of 5 crore INR", "IN", 0.7),
        
        # Default case (no indicators)
        ("What is theft?", "IN", 0.5),
        ("Legal advice needed", "IN", 0.5),
    ]
    
    print("Testing Indian Jurisdiction Detection")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query, expected_jurisdiction, min_confidence in test_cases:
        result = detector.detect(query)
        
        if result.jurisdiction == expected_jurisdiction and result.confidence >= min_confidence:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"{status}: '{query}'")
        print(f"  Expected: {expected_jurisdiction} (>={min_confidence})")
        print(f"  Got: {result.jurisdiction} ({result.confidence:.2f})")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_user_hint_precedence():
    """Test that user-provided hints take precedence"""
    detector = JurisdictionDetector()
    
    print("\nTesting User Hint Precedence")
    print("=" * 60)
    
    # Query with strong Indian indicators but UK hint
    query = "Section 498A IPC dowry harassment in Mumbai"
    result_no_hint = detector.detect(query)
    result_with_hint = detector.detect(query, user_hint="UK")
    
    print(f"Query: '{query}'")
    print(f"Without hint: {result_no_hint.jurisdiction} ({result_no_hint.confidence:.2f})")
    print(f"With UK hint: {result_with_hint.jurisdiction} ({result_with_hint.confidence:.2f})")
    
    assert result_no_hint.jurisdiction == "IN", "Should detect IN without hint"
    assert result_with_hint.jurisdiction == "UK", "Should use UK with hint"
    assert result_with_hint.confidence == 1.0, "User hint should have 1.0 confidence"
    
    print("PASS: User hint takes precedence\n")
    return True


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    detector = JurisdictionDetector()
    
    print("Testing Edge Cases")
    print("=" * 60)
    
    test_cases = [
        ("", "IN", 0.5),  # Empty query
        ("   ", "IN", 0.5),  # Whitespace only
        ("IPC IPC IPC IPC IPC", "IN", 0.9),  # Repeated keywords
        ("ipc bns crpc bnss", "IN", 0.9),  # Multiple strong indicators
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_jurisdiction, min_confidence in test_cases:
        result = detector.detect(query)
        
        if result.jurisdiction == expected_jurisdiction:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
        
        print(f"{status}: '{query}'")
        print(f"  Expected: {expected_jurisdiction}")
        print(f"  Got: {result.jurisdiction} ({result.confidence:.2f})")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_confidence_scoring():
    """Test confidence scoring mechanism"""
    detector = JurisdictionDetector()
    
    print("Testing Confidence Scoring")
    print("=" * 60)
    
    queries = [
        ("Section 498A IPC dowry harassment FIR", "Very High"),  # Multiple strong indicators
        ("Property dispute in Delhi", "Medium"),  # Geographic only
        ("Legal advice needed", "Low/Default"),  # No indicators
    ]
    
    for query, expected_level in queries:
        result = detector.detect(query)
        print(f"Query: '{query}'")
        print(f"  Confidence: {result.confidence:.2f} ({expected_level})")
        print(f"  Jurisdiction: {result.jurisdiction}")
        print()
    
    return True


def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 60)
    print("JURISDICTION DETECTOR TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_indian_jurisdiction_detection,
        test_user_hint_precedence,
        test_edge_cases,
        test_confidence_scoring
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"ERROR in {test.__name__}: {e}\n")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("All tests PASSED")
    else:
        print("Some tests FAILED")
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
