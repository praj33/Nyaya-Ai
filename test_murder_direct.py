import sys
import os
sys.path.append('.')

from clean_legal_advisor import EnhancedLegalAdvisor, LegalQuery

def test_murder_direct():
    print("=" * 80)
    print("TESTING MURDER/KILLING QUERY (DIRECT)")
    print("=" * 80)
    
    advisor = EnhancedLegalAdvisor()
    
    query = LegalQuery(
        query_text="someone killed my friend",
        jurisdiction_hint="India",
        domain_hint="criminal"
    )
    
    print(f"\nQuery: {query.query_text}")
    print(f"Jurisdiction Hint: {query.jurisdiction_hint}")
    print(f"Domain Hint: {query.domain_hint}")
    
    advice = advisor.provide_legal_advice(query)
    
    print("\n" + "=" * 80)
    print("RESPONSE DETAILS")
    print("=" * 80)
    
    print(f"\nJurisdiction: {advice.jurisdiction}")
    print(f"Domain: {advice.domain}")
    print(f"Domains: {advice.domains if hasattr(advice, 'domains') else [advice.domain]}")
    print(f"Confidence: {advice.confidence_score:.2f}")
    
    print(f"\n[STATUTES] Found {len(advice.statutes)} statutes:")
    for statute in advice.statutes:
        print(f"  - {statute.get('act')} ({statute.get('year')})")
        print(f"    Section {statute.get('section')}: {statute.get('title')}")
    
    if advice.constitutional_articles:
        print(f"\n[CONSTITUTIONAL ARTICLES] {len(advice.constitutional_articles)} articles:")
        for article in advice.constitutional_articles:
            print(f"  - {article}")
    
    print(f"\n[RELEVANT SECTIONS] {len(advice.relevant_sections)} sections:")
    for section in advice.relevant_sections[:5]:
        print(f"  - Section {section.section_number} ({section.act_id})")
        print(f"    {section.text[:100]}...")
    
    print(f"\n[PROCEDURAL STEPS] {len(advice.procedural_steps)} steps:")
    for i, step in enumerate(advice.procedural_steps, 1):
        print(f"  {i}. {step}")
    
    print(f"\n[REMEDIES] {len(advice.remedies)} remedies:")
    for i, remedy in enumerate(advice.remedies, 1):
        print(f"  {i}. {remedy}")
    
    print(f"\n[LEGAL ANALYSIS]")
    print(advice.legal_analysis)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_murder_direct()
