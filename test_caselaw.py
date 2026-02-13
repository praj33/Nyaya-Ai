import sys
sys.path.append('.')

from core.caselaw.loader import CaseLawLoader
from core.caselaw.retriever import CaseLawRetriever

def test_case_law_loading():
    """Test case law loading"""
    loader = CaseLawLoader()
    cases = loader.load_all()
    
    print(f"Loaded {len(cases)} cases")
    
    assert len(cases) > 0, "Should load at least some cases"
    
    # Check structure
    for case in cases[:3]:
        print(f"\nCase: {case.title}")
        print(f"  Court: {case.court}")
        print(f"  Year: {case.year}")
        print(f"  Domain: {case.domain}")
        print(f"  Keywords: {', '.join(case.keywords[:5])}")
        
        assert case.title, "Case must have title"
        assert case.court, "Case must have court"
        assert case.year > 0, "Case must have valid year"
        assert case.jurisdiction, "Case must have jurisdiction"
        assert case.domain, "Case must have domain"
    
    print("\nOK: Case law loading test passed!")

def test_case_law_retrieval():
    """Test case law retrieval for dowry harassment query"""
    loader = CaseLawLoader()
    cases = loader.load_all()
    retriever = CaseLawRetriever(cases)
    
    query = "my husband is harassing me for dowry"
    
    relevant_cases = retriever.retrieve(
        query=query,
        domain="criminal",
        jurisdiction="IN",
        top_k=3
    )
    
    print(f"\nQuery: {query}")
    print(f"Retrieved {len(relevant_cases)} cases:")
    
    for i, case in enumerate(relevant_cases, 1):
        print(f"\n{i}. {case.title}")
        print(f"   Court: {case.court}")
        print(f"   Year: {case.year}")
        print(f"   Principle: {case.principle[:100]}...")
    
    assert len(relevant_cases) > 0, "Should retrieve at least one case"
    
    # Check that 498A cases are retrieved
    case_titles = [case.title.lower() for case in relevant_cases]
    case_principles = [case.principle.lower() for case in relevant_cases]
    
    has_498a_case = any('498a' in title or 'cruelty' in title or 'dowry' in title 
                        for title in case_titles)
    has_498a_principle = any('498a' in principle or 'dowry' in principle 
                            for principle in case_principles)
    
    assert has_498a_case or has_498a_principle, "Should retrieve 498A/dowry related cases"
    
    print("\nOK: Case law retrieval test passed!")

def test_family_case_retrieval():
    """Test case law retrieval for divorce query"""
    loader = CaseLawLoader()
    cases = loader.load_all()
    retriever = CaseLawRetriever(cases)
    
    query = "I want to file for divorce due to cruelty"
    
    relevant_cases = retriever.retrieve(
        query=query,
        domain="family",
        jurisdiction="IN",
        top_k=3
    )
    
    print(f"\nQuery: {query}")
    print(f"Retrieved {len(relevant_cases)} family law cases:")
    
    for i, case in enumerate(relevant_cases, 1):
        print(f"\n{i}. {case.title}")
        print(f"   Principle: {case.principle[:100]}...")
    
    assert len(relevant_cases) > 0, "Should retrieve family law cases"
    
    print("\nOK: Family case retrieval test passed!")

if __name__ == "__main__":
    test_case_law_loading()
    test_case_law_retrieval()
    test_family_case_retrieval()
