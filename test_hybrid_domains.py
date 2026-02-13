import sys
sys.path.append('.')

from core.ontology.statute_resolver import StatuteResolver
from clean_legal_advisor import EnhancedLegalAdvisor, LegalQuery

def test_marital_cruelty_detection():
    """Test that dowry harassment is classified as criminal+family hybrid"""
    
    advisor = EnhancedLegalAdvisor()
    resolver = StatuteResolver()
    
    # Test query
    query = "my husband is harassing me for dowry"
    
    # Detect domains
    domains = advisor._detect_domains(query, None)
    
    print(f"Query: {query}")
    print(f"Detected domains: {domains}")
    
    assert 'criminal' in domains, "Criminal domain must be detected"
    assert 'family' in domains, "Family domain must be detected"
    assert domains[0] == 'criminal', "Criminal must be primary domain"
    
    # Check offense category detection
    offense_category = resolver.detect_offense_category(query)
    
    print(f"Offense category: {offense_category}")
    
    assert offense_category is not None, "Marital cruelty category must be detected"
    assert offense_category['primary_domain'] == 'criminal', "Primary domain must be criminal"
    
    # Get relevant acts
    relevant_acts = resolver.get_relevant_acts(query, domains, "IN")
    
    print(f"Relevant acts: {relevant_acts}")
    
    assert 'bns_sections' in relevant_acts or 'ipc_sections' in relevant_acts, "BNS/IPC must be included"
    assert 'dowry_prohibition_act' in relevant_acts, "Dowry Prohibition Act must be included"
    assert 'domestic_violence_act' in relevant_acts, "Domestic Violence Act must be included"
    
    print("\nOK: All tests passed!")

def test_full_query_flow():
    """Test full query flow for dowry harassment"""
    
    advisor = EnhancedLegalAdvisor()
    
    query = LegalQuery(
        query_text="my husband is harassing me for dowry",
        jurisdiction_hint="India",
        domain_hint="criminal"
    )
    
    advice = advisor.provide_legal_advice(query)
    
    print(f"\nFull Query Test:")
    print(f"Query: {query.query_text}")
    print(f"Primary domain: {advice.domain}")
    print(f"All domains: {advice.domains if hasattr(advice, 'domains') else [advice.domain]}")
    print(f"Sections found: {len(advice.relevant_sections)}")
    print(f"Confidence: {advice.confidence_score}")
    
    # Check sections
    section_acts = set()
    for section in advice.relevant_sections[:10]:
        section_acts.add(section.act_id)
        print(f"  - {section.section_number} ({section.act_id}): {section.text[:80]}...")
    
    print(f"\nActs represented: {section_acts}")
    
    # Verify procedural steps mention both criminal and family proceedings
    procedural_text = " ".join(advice.procedural_steps).lower()
    
    assert 'fir' in procedural_text or 'police' in procedural_text, "Must mention FIR/police"
    assert 'protection order' in procedural_text or 'domestic violence' in procedural_text, "Must mention DV Act remedies"
    
    print("\nOK: Full query flow test passed!")

if __name__ == "__main__":
    test_marital_cruelty_detection()
    test_full_query_flow()
