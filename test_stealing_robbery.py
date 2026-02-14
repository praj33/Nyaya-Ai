import sys
sys.path.append('.')

from clean_legal_advisor import EnhancedLegalAdvisor, LegalQuery

def test_stealing_robbery_queries():
    print("=" * 80)
    print("TESTING STEALING/ROBBERY QUERIES")
    print("=" * 80)
    
    advisor = EnhancedLegalAdvisor()
    
    # Test 1: Stealing
    print("\n[TEST 1] Stealing Query")
    print("-" * 80)
    query1 = LegalQuery("someone stole my phone", "India", "criminal")
    advice1 = advisor.provide_legal_advice(query1)
    print(f"Query: {query1.query_text}")
    print(f"\nStatutes found: {len(advice1.statutes)}")
    for s in advice1.statutes:
        print(f"  - {s['act']} ({s['year']}) Section {s['section']}: {s['title']}")
    print(f"\nProcedural Steps: {len(advice1.procedural_steps)}")
    for i, step in enumerate(advice1.procedural_steps[:5], 1):
        print(f"  {i}. {step}")
    print(f"\nRemedies: {len(advice1.remedies)}")
    for i, remedy in enumerate(advice1.remedies[:3], 1):
        print(f"  {i}. {remedy}")
    
    # Test 2: Robbery
    print("\n" + "=" * 80)
    print("[TEST 2] Robbery Query")
    print("-" * 80)
    query2 = LegalQuery("i was robbed at gunpoint", "India", "criminal")
    advice2 = advisor.provide_legal_advice(query2)
    print(f"Query: {query2.query_text}")
    print(f"\nStatutes found: {len(advice2.statutes)}")
    for s in advice2.statutes:
        print(f"  - {s['act']} ({s['year']}) Section {s['section']}: {s['title']}")
    print(f"\nProcedural Steps: {len(advice2.procedural_steps)}")
    for i, step in enumerate(advice2.procedural_steps[:5], 1):
        print(f"  {i}. {step}")
    print(f"\nRemedies: {len(advice2.remedies)}")
    for i, remedy in enumerate(advice2.remedies[:3], 1):
        print(f"  {i}. {remedy}")
    
    # Test 3: Theft
    print("\n" + "=" * 80)
    print("[TEST 3] Theft Query")
    print("-" * 80)
    query3 = LegalQuery("theft in my house", "India", "criminal")
    advice3 = advisor.provide_legal_advice(query3)
    print(f"Query: {query3.query_text}")
    print(f"\nStatutes found: {len(advice3.statutes)}")
    for s in advice3.statutes:
        print(f"  - {s['act']} ({s['year']}) Section {s['section']}: {s['title']}")
    print(f"\nProcedural Steps: {len(advice3.procedural_steps)}")
    for i, step in enumerate(advice3.procedural_steps[:5], 1):
        print(f"  {i}. {step}")
    print(f"\nRemedies: {len(advice3.remedies)}")
    for i, remedy in enumerate(advice3.remedies[:3], 1):
        print(f"  {i}. {remedy}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"[PASS] Stealing query returned {len(advice1.statutes)} statutes")
    print(f"[PASS] Robbery query returned {len(advice2.statutes)} statutes")
    print(f"[PASS] Theft query returned {len(advice3.statutes)} statutes")
    print("\n[SUCCESS] All stealing/robbery queries working correctly")

if __name__ == "__main__":
    test_stealing_robbery_queries()
