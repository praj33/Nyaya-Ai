"""
Test suite for dowry_demand vs dowry_death distinction
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ontology.statute_resolver import StatuteResolver


def test_dowry_demand_no_death_sections():
    """Test dowry demand queries never return death sections"""
    resolver = StatuteResolver()
    
    test_cases = [
        "my husband is asking for dowry",
        "husband demanding money from my parents",
        "husband beating me for dowry",
        "498a harassment case",
        "dowry torture by in-laws",
        "my husband is asking for money",
        "demanding cash from family"
    ]
    
    print("Testing Dowry Demand (No Death Sections)")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query in test_cases:
        category = resolver.detect_offense_category(query)
        
        if category:
            # Check for BNS 85 (cruelty) - should be present
            has_cruelty = any(
                '85' in str(s.get('sections', []))
                for s in category.get('primary_statutes', [])
                if s.get('act_id') == 'bns_sections'
            )
            
            # Check for BNS 80 (death) - should NOT be present
            has_death = any(
                '80' in str(s.get('sections', []))
                for s in category.get('primary_statutes', [])
                if s.get('act_id') == 'bns_sections'
            )
            
            # Check for DPA 4 (demanding dowry) - should be present
            has_dpa4 = any(
                '4' in str(s.get('sections', []))
                for s in category.get('primary_statutes', [])
                if s.get('act_id') == 'dowry_prohibition_act'
            )
            
            if has_cruelty and not has_death and has_dpa4:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1
                print(f"{status}: '{query}'")
                print(f"  Has BNS 85 (cruelty): {has_cruelty} (expected: True)")
                print(f"  Has BNS 80 (death): {has_death} (expected: False)")
                print(f"  Has DPA 4 (demand): {has_dpa4} (expected: True)")
                continue
            
            print(f"{status}: '{query}'")
            print(f"  Category: dowry_demand")
            print(f"  BNS 85 included: {has_cruelty}")
            print(f"  BNS 80 excluded: {not has_death}")
            print(f"  DPA 4 included: {has_dpa4}")
        else:
            status = "FAIL"
            failed += 1
            print(f"{status}: '{query}'")
            print(f"  No category detected")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_dowry_death_requires_death_keywords():
    """Test dowry death requires death keywords"""
    resolver = StatuteResolver()
    
    test_cases = [
        ("wife died due to dowry harassment", True, True, False),
        ("she was burnt for dowry", True, True, False),
        ("found dead after dowry torture", True, True, False),
        ("suicide due to dowry demands", True, True, False),
        ("killed for not bringing dowry", True, True, False),
        ("body found with burn marks dowry", True, True, False),
        ("dowry harassment", False, False, True),  # Should be dowry_demand
        ("asking for dowry", False, False, True),  # Should be dowry_demand
        ("husband demanding money", False, False, True)  # Should be dowry_demand
    ]
    
    print("Testing Dowry Death Detection")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for query, should_have_death, should_have_bns80, should_have_bns85 in test_cases:
        category = resolver.detect_offense_category(query)
        
        if category:
            has_bns80 = any(
                '80' in str(s.get('sections', []))
                for s in category.get('primary_statutes', [])
                if s.get('act_id') == 'bns_sections'
            )
            
            has_bns85 = any(
                '85' in str(s.get('sections', []))
                for s in category.get('primary_statutes', [])
                if s.get('act_id') == 'bns_sections'
            )
            
            if has_bns80 == should_have_bns80 and has_bns85 == should_have_bns85:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1
        else:
            if not should_have_death:
                status = "PASS"
                passed += 1
            else:
                status = "FAIL"
                failed += 1
        
        print(f"{status}: '{query}'")
        if category:
            print(f"  Expected BNS 80: {should_have_bns80}, Got: {has_bns80}")
            print(f"  Expected BNS 85: {should_have_bns85}, Got: {has_bns85}")
        else:
            print(f"  No category detected (expected: {should_have_death})")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_penal_code_exclusivity():
    """Test penal code exclusivity still works"""
    resolver = StatuteResolver()
    
    print("Testing Penal Code Exclusivity")
    print("=" * 60)
    
    query = "husband asking for dowry"
    domains = ["criminal", "family"]
    
    # Test 2024+
    acts_2024 = resolver.get_relevant_acts(query, domains, jurisdiction_year=2024)
    has_bns = 'bns_sections' in acts_2024
    has_ipc = 'ipc_sections' in acts_2024
    
    status_2024 = "PASS" if (has_bns and not has_ipc) else "FAIL"
    print(f"{status_2024}: Year 2024")
    print(f"  BNS included: {has_bns}")
    print(f"  IPC blocked: {not has_ipc}")
    print()
    
    # Test 2023
    acts_2023 = resolver.get_relevant_acts(query, domains, jurisdiction_year=2023)
    has_bns = 'bns_sections' in acts_2023
    has_ipc = 'ipc_sections' in acts_2023
    
    status_2023 = "PASS" if (has_ipc and not has_bns) else "FAIL"
    print(f"{status_2023}: Year 2023")
    print(f"  IPC included: {has_ipc}")
    print(f"  BNS blocked: {not has_bns}")
    print()
    
    return status_2024 == "PASS" and status_2023 == "PASS"


def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 60)
    print("DOWRY DEMAND VS DOWRY DEATH TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_dowry_demand_no_death_sections,
        test_dowry_death_requires_death_keywords,
        test_penal_code_exclusivity
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
