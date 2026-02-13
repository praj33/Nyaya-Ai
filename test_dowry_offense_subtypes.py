"""
Test suite for dowry offense subtypes and penal code exclusivity
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ontology.statute_resolver import StatuteResolver


def test_dowry_harassment_detection():
    """Test dowry harassment detection (no death keywords)"""
    resolver = StatuteResolver()
    
    test_cases = [
        "my husband is asking for dowry",
        "husband demanding money from my parents",
        "husband beating me for dowry",
        "498a harassment case",
        "dowry torture by in-laws"
    ]
    
    print("Testing Dowry Harassment Detection")
    print("=" * 60)
    
    for query in test_cases:
        category = resolver.detect_offense_category(query)
        
        if category:
            has_death_sections = any(
                '80' in str(s.get('sections', [])) or '304B' in str(s.get('sections', []))
                for s in category.get('primary_statutes', [])
            )
            status = "FAIL" if has_death_sections else "PASS"
        else:
            status = "FAIL"
        
        print(f"{status}: '{query}'")
        if category:
            print(f"  Category detected: dowry_harassment")
            print(f"  Constitutional Articles: {category.get('constitutional_articles', [])}")
            print(f"  Death sections excluded: {not has_death_sections}")
        print()
    
    return True


def test_dowry_death_detection():
    """Test dowry death detection (requires death keywords)"""
    resolver = StatuteResolver()
    
    test_cases = [
        ("wife died due to dowry harassment", True),
        ("she was burnt for dowry", True),
        ("found dead after dowry torture", True),
        ("suicide due to dowry demands", True),
        ("killed for not bringing dowry", True),
        ("dowry harassment", False),  # Should NOT trigger dowry_death
        ("asking for dowry", False)   # Should NOT trigger dowry_death
    ]
    
    print("Testing Dowry Death Detection")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query, should_detect_death in test_cases:
        category = resolver.detect_offense_category(query)
        
        if category:
            has_death_sections = any(
                '80' in str(s.get('sections', [])) or '304B' in str(s.get('sections', []))
                for s in category.get('primary_statutes', [])
            )
            
            if should_detect_death == has_death_sections:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1
        else:
            if not should_detect_death:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1
        
        print(f"{status}: '{query}'")
        print(f"  Expected death sections: {should_detect_death}")
        if category:
            print(f"  Got death sections: {has_death_sections}")
            print(f"  Constitutional Articles: {category.get('constitutional_articles', [])}")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_penal_code_exclusivity_2024():
    """Test BNS used for 2024+, IPC blocked"""
    resolver = StatuteResolver()
    
    print("Testing Penal Code Exclusivity (2024+)")
    print("=" * 60)
    
    query = "husband asking for dowry"
    domains = ["criminal", "family"]
    
    # Test for year 2024
    acts_2024 = resolver.get_relevant_acts(query, domains, jurisdiction_year=2024)
    
    has_bns = 'bns_sections' in acts_2024
    has_ipc = 'ipc_sections' in acts_2024
    
    status = "PASS" if (has_bns and not has_ipc) else "FAIL"
    
    print(f"{status}: Year 2024")
    print(f"  BNS included: {has_bns}")
    print(f"  IPC blocked: {not has_ipc}")
    print(f"  Acts: {acts_2024}")
    print()
    
    return has_bns and not has_ipc


def test_penal_code_exclusivity_2023():
    """Test IPC used for pre-2024, BNS blocked"""
    resolver = StatuteResolver()
    
    print("Testing Penal Code Exclusivity (Pre-2024)")
    print("=" * 60)
    
    query = "husband asking for dowry"
    domains = ["criminal", "family"]
    
    # Test for year 2023
    acts_2023 = resolver.get_relevant_acts(query, domains, jurisdiction_year=2023)
    
    has_bns = 'bns_sections' in acts_2023
    has_ipc = 'ipc_sections' in acts_2023
    
    status = "PASS" if (has_ipc and not has_bns) else "FAIL"
    
    print(f"{status}: Year 2023")
    print(f"  IPC included: {has_ipc}")
    print(f"  BNS blocked: {not has_bns}")
    print(f"  Acts: {acts_2023}")
    print()
    
    return has_ipc and not has_bns


def test_constitutional_articles():
    """Test constitutional articles for dignity cases"""
    resolver = StatuteResolver()
    
    print("Testing Constitutional Articles")
    print("=" * 60)
    
    test_cases = [
        "husband asking for dowry",
        "wife died due to dowry"
    ]
    
    for query in test_cases:
        category = resolver.detect_offense_category(query)
        
        if category:
            articles = category.get('constitutional_articles', [])
            has_article_21 = 'Article 21' in articles
            has_article_15_3 = 'Article 15(3)' in articles
            
            status = "PASS" if (has_article_21 and has_article_15_3) else "FAIL"
        else:
            status = "FAIL"
        
        print(f"{status}: '{query}'")
        if category:
            print(f"  Constitutional Articles: {articles}")
        print()
    
    return True


def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 60)
    print("DOWRY OFFENSE SUBTYPES & PENAL CODE EXCLUSIVITY TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_dowry_harassment_detection,
        test_dowry_death_detection,
        test_penal_code_exclusivity_2024,
        test_penal_code_exclusivity_2023,
        test_constitutional_articles
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
