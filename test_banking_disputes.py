import sys
sys.path.append('.')

from clean_legal_advisor import EnhancedLegalAdvisor, LegalQuery
from dispute_type_matcher import DisputeTypeMatcher

def test_banking_disputes():
    print("=" * 80)
    print("TESTING BANKING DISPUTES QUERY")
    print("=" * 80)
    
    advisor = EnhancedLegalAdvisor()
    matcher = DisputeTypeMatcher()
    
    query = LegalQuery("bank refused to release my fixed deposit", "India", "civil")
    advice = advisor.provide_legal_advice(query)
    
    # Get dispute-specific information
    dispute_type = matcher.detect_dispute_type(query.query_text)
    dispute_info = matcher.get_dispute_info(dispute_type) if dispute_type else None
    
    print(f"\nQuery: {query.query_text}")
    print(f"Domain: {advice.domain}")
    print(f"Jurisdiction: {advice.jurisdiction}")
    print(f"Confidence: {advice.confidence_score:.2f}")
    
    print(f"\n{'='*80}")
    print("STATUTES/LAWS APPLICABLE")
    print('='*80)
    print(f"Total statutes found: {len(advice.statutes)}")
    for i, s in enumerate(advice.statutes, 1):
        print(f"\n{i}. {s['act']} ({s['year']})")
        print(f"   Section: {s['section']}")
        print(f"   Title: {s['title']}")
    
    print(f"\n{'='*80}")
    print("PROCEDURAL STEPS")
    print('='*80)
    print(f"Total steps: {len(advice.procedural_steps)}")
    for i, step in enumerate(advice.procedural_steps, 1):
        print(f"{i}. {step}")
    
    print(f"\n{'='*80}")
    print("REMEDIES AVAILABLE")
    print('='*80)
    print(f"Total remedies: {len(advice.remedies)}")
    for i, remedy in enumerate(advice.remedies, 1):
        print(f"{i}. {remedy}")
    
    print(f"\n{'='*80}")
    print("LEGAL ANALYSIS")
    print('='*80)
    print(advice.legal_analysis)
    
    # Check if banking-specific information is present
    print(f"\n{'='*80}")
    print("BANKING DISPUTE SPECIFIC INFORMATION FROM indian_law_dataset.json")
    print('='*80)
    
    if dispute_info:
        print(f"\nDispute Type Detected: {dispute_type}")
        print(f"\nApplicable Law: {dispute_info.get('law', 'N/A')}")
        
        print(f"\nRemedies from Dataset:")
        for i, remedy in enumerate(dispute_info.get('remedies', []), 1):
            print(f"{i}. {remedy}")
        
        print(f"\nProcess Steps from Dataset:")
        for i, step in enumerate(dispute_info.get('process_steps', []), 1):
            print(f"{i}. {step}")
    else:
        print("\nNo specific dispute type detected")
    
    # Check database for banking laws
    banking_sections = [s for s in advisor.sections if 'bank' in s.text.lower() or 'bank' in s.act_id.lower()]
    print(f"\nBanking-related sections in database: {len(banking_sections)}")
    if banking_sections:
        print("\nSample banking sections:")
        for s in banking_sections[:5]:
            print(f"  - {s.act_id} Section {s.section_number}: {s.text[:80]}...")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    print(f"[INFO] Query processed successfully")
    print(f"[INFO] Domain detected: {advice.domain}")
    print(f"[INFO] Statutes found: {len(advice.statutes)}")
    print(f"[INFO] Procedural steps: {len(advice.procedural_steps)}")
    print(f"[INFO] Remedies: {len(advice.remedies)}")

if __name__ == "__main__":
    test_banking_disputes()
