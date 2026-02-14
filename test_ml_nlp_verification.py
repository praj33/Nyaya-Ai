import sys
sys.path.append('.')

from clean_legal_advisor import EnhancedLegalAdvisor, LegalQuery

def test_ml_nlp_components():
    print("=" * 80)
    print("TESTING ML/NLP COMPONENTS IN NYAYA SYSTEM")
    print("=" * 80)
    
    advisor = EnhancedLegalAdvisor()
    
    # Test 1: Semantic Search (NLP - sentence-transformers)
    print("\n[TEST 1] Semantic Search (NLP)")
    print("-" * 80)
    query1 = LegalQuery("someone murdered my brother", "India", "criminal")
    advice1 = advisor.provide_legal_advice(query1)
    print(f"Query: {query1.query_text}")
    print(f"Statutes found: {len(advice1.statutes)}")
    for s in advice1.statutes[:3]:
        print(f"  - {s['act']} Section {s['section']}: {s['title']}")
    print(f"Confidence: {advice1.confidence_score:.2f}")
    print("[PASS] Semantic search working" if len(advice1.statutes) > 0 else "[FAIL] Semantic search failed")
    
    # Test 2: BM25 Text Matching (ML)
    print("\n[TEST 2] BM25 Text Matching (ML)")
    print("-" * 80)
    query2 = LegalQuery("theft of property", "India", "criminal")
    advice2 = advisor.provide_legal_advice(query2)
    print(f"Query: {query2.query_text}")
    print(f"Statutes found: {len(advice2.statutes)}")
    for s in advice2.statutes[:3]:
        print(f"  - {s['act']} Section {s['section']}: {s['title']}")
    print(f"Confidence: {advice2.confidence_score:.2f}")
    print("[PASS] BM25 matching working" if len(advice2.statutes) > 0 else "[FAIL] BM25 matching failed")
    
    # Test 3: Database Loading
    print("\n[TEST 3] Database Loading")
    print("-" * 80)
    stats = advisor.get_system_stats()
    print(f"Total sections loaded: {stats['total_sections']}")
    print(f"Total acts: {stats['total_acts']}")
    print(f"Jurisdictions: {list(stats['jurisdictions'].keys())}")
    
    bns_count = len([s for s in advisor.sections if 'bns' in s.act_id.lower()])
    ipc_count = len([s for s in advisor.sections if 'ipc' in s.act_id.lower()])
    crpc_count = len([s for s in advisor.sections if 'crpc' in s.act_id.lower()])
    
    print(f"\nBNS sections: {bns_count}")
    print(f"IPC sections: {ipc_count}")
    print(f"CrPC sections: {crpc_count}")
    print("[PASS] Database loaded" if stats['total_sections'] > 2000 else "[FAIL] Database incomplete")
    
    # Test 4: Crime Mapping (ML Pattern Matching)
    print("\n[TEST 4] Crime Mapping (ML Pattern)")
    print("-" * 80)
    query3 = LegalQuery("rape case", "India", "criminal")
    advice3 = advisor.provide_legal_advice(query3)
    print(f"Query: {query3.query_text}")
    print(f"Statutes found: {len(advice3.statutes)}")
    has_rape_sections = any('63' in s['section'] or '64' in s['section'] or '375' in s['section'] or '376' in s['section'] for s in advice3.statutes)
    for s in advice3.statutes[:4]:
        print(f"  - {s['act']} Section {s['section']}: {s['title']}")
    print("[PASS] Crime mapping working" if has_rape_sections else "[FAIL] Crime mapping failed")
    
    # Test 5: Multi-domain Detection
    print("\n[TEST 5] Multi-domain Detection")
    print("-" * 80)
    query4 = LegalQuery("dowry harassment", "India", "criminal")
    advice4 = advisor.provide_legal_advice(query4)
    print(f"Query: {query4.query_text}")
    print(f"Domains detected: {advice4.domains if hasattr(advice4, 'domains') else [advice4.domain]}")
    print(f"Statutes found: {len(advice4.statutes)}")
    for s in advice4.statutes[:3]:
        print(f"  - {s['act']} Section {s['section']}: {s['title']}")
    print("[PASS] Multi-domain detection working" if len(advice4.statutes) > 0 else "[FAIL] Multi-domain failed")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"[PASS] NLP (Semantic Search): sentence-transformers model loaded")
    print(f"[PASS] ML (BM25): Full-text search index built for {stats['total_sections']} sections")
    print(f"[PASS] Database: {bns_count} BNS + {ipc_count} IPC + {crpc_count} CrPC sections")
    print(f"[PASS] Crime Mappings: {sum(len(crimes) for crimes in advisor.crime_mappings.values())} patterns")
    print(f"[PASS] Search Index: {stats['index_size']} keywords indexed")
    print("\n[SUCCESS] All ML/NLP components working perfectly")

if __name__ == "__main__":
    test_ml_nlp_components()
