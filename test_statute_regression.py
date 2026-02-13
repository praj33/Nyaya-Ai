#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from enhanced_legal_advisor import EnhancedLegalAdvisor, LegalQuery

def test_dowry_demand_regression():
    """Regression test: dowry demand should return >= 3 statutes"""
    advisor = EnhancedLegalAdvisor()
    
    query = LegalQuery("dowry demand", "India", "criminal")
    advice = advisor.provide_legal_advice(query)
    
    print(f"Query: {query.query_text}")
    print(f"Statutes found: {len(advice.relevant_sections)}")
    print(f"Jurisdiction: {advice.jurisdiction}")
    print(f"Domain: {advice.domain}")
    
    if advice.relevant_sections:
        print("Sections found:")
        for i, section in enumerate(advice.relevant_sections[:5], 1):
            print(f"  {i}. Section {section.section_number}: {section.text[:50]}...")
    
    # Regression test assertion
    assert len(advice.relevant_sections) >= 3, f"Expected >= 3 statutes for dowry demand, got {len(advice.relevant_sections)}"
    print("[PASS] Dowry demand regression test PASSED")
    
    return len(advice.relevant_sections)

if __name__ == "__main__":
    print("Running statute retrieval regression test...")
    sections_found = test_dowry_demand_regression()
    print(f"Regression test completed successfully! Found {sections_found} statutes.")