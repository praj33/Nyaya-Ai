import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.vector.faiss_search import FAISSSearch
from core.ontology.statute_resolver import StatuteResolver

def test_semantic_search():
    print("=" * 80)
    print("FAISS SEMANTIC SEARCH TEST")
    print("=" * 80)
    
    # Test 1: Direct FAISS search
    print("\n[Test 1] Direct FAISS Search")
    print("Query: 'husband forcing money'")
    
    faiss_search = FAISSSearch()
    faiss_search.load_indexes()
    
    results = faiss_search.search_statutes("husband forcing money", k=5)
    
    if results:
        print(f"Found {len(results)} results:")
        for meta, score in results:
            print(f"  - {meta.get('act', 'N/A')} Section {meta.get('section', 'N/A')} (score: {score:.4f})")
    else:
        print("No results found (indexes may not be built yet)")
    
    # Test 2: Integrated with resolver
    print("\n[Test 2] Integrated with StatuteResolver")
    print("Query: 'husband forcing money'")
    
    resolver = StatuteResolver(use_faiss=True)
    subtype = resolver.detect_offense_subtype("husband forcing money")
    
    if not subtype:
        # Try with more explicit query
        subtype = resolver.detect_offense_subtype("husband demanding money")
    
    if subtype:
        print(f"Detected subtype: {subtype}")
        subtype_data = resolver.offense_subtypes[subtype]
        print(f"Expected statutes:")
        for statute in subtype_data['statutes']:
            print(f"  - {statute['act']} Section {statute['section']}")
    else:
        print("No subtype detected, checking offense categories...")
        category = resolver.detect_offense_category("husband demanding money")
        if category:
            print("Found offense category")
    
    # Test 3: Dowry Prohibition Act Section 4
    print("\n[Test 3] Validation")
    print("Expected: Dowry Prohibition Act Section 4")
    
    # Use explicit dowry query
    test_query = "husband demanding money"
    subtype = resolver.detect_offense_subtype(test_query)
    
    if subtype and subtype in resolver.offense_subtypes:
        statutes = resolver.offense_subtypes[subtype]['statutes']
        found = any(
            'Dowry Prohibition Act' in s['act'] and s['section'] == '4'
            for s in statutes
        )
        if found:
            print(f"[PASS] Dowry Prohibition Act Section 4 found in subtype '{subtype}'")
        else:
            print(f"[FAIL] Dowry Prohibition Act Section 4 not found in subtype '{subtype}'")
    else:
        print(f"[FAIL] No subtype detected for query: {test_query}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_semantic_search()
