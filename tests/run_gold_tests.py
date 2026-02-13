import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ontology.statute_resolver import StatuteResolver

def load_gold_cases(gold_cases_dir):
    cases = []
    for json_file in gold_cases_dir.glob("*.json"):
        if json_file.name == "schema.json":
            continue
        with open(json_file, 'r', encoding='utf-8') as f:
            file_cases = json.load(f)
            cases.extend(file_cases)
    return cases

def run_gold_tests():
    resolver = StatuteResolver(use_faiss=False)
    gold_cases_dir = Path(__file__).parent / "gold_cases"
    
    cases = load_gold_cases(gold_cases_dir)
    passed = 0
    failed = 0
    
    print("=" * 80)
    print("GOLD LEGAL TEST SUITE")
    print("=" * 80)
    
    for case in cases:
        case_id = case['id']
        query = case['query']
        expected_domains = set(case['expected_domains'])
        must_include = case['must_include_statutes']
        must_not_include = case.get('must_not_include_statutes', [])
        
        subtype = resolver.detect_offense_subtype(query)
        category = resolver.detect_offense_category(query)
        
        if subtype and subtype in resolver.offense_subtypes:
            detected_domains = set(resolver.offense_subtypes[subtype]['domains'])
        elif category:
            detected_domains = set(category.get('domains', []))
        else:
            detected_domains = set()
        
        acts = resolver.get_relevant_acts(query, list(detected_domains), jurisdiction_year=2024)
        
        statutes = []
        if subtype and subtype in resolver.offense_subtypes:
            statutes = resolver.offense_subtypes[subtype]['statutes']
        elif category:
            for sg in category.get('primary_statutes', []):
                act_id = sg['act_id']
                if act_id in acts:
                    act_name = resolver.acts[act_id]['name']
                    for section in sg['sections']:
                        statutes.append({'act': act_name, 'section': section})
        
        errors = []
        
        if not expected_domains.issubset(detected_domains):
            errors.append(f"Domain mismatch. Expected {expected_domains}, got {detected_domains}")
        
        for required in must_include:
            found = any(
                s['act'] == required['act'] and s['section'] == required['section']
                for s in statutes
            )
            if not found:
                errors.append(f"Missing: {required['act']} Section {required['section']}")
        
        for forbidden in must_not_include:
            found = any(
                s['act'] == forbidden['act'] and s['section'] == forbidden['section']
                for s in statutes
            )
            if found:
                errors.append(f"Forbidden: {forbidden['act']} Section {forbidden['section']}")
        
        if errors:
            print(f"\n[FAIL] {case_id}")
            print(f"  Query: {query}")
            for error in errors:
                print(f"  - {error}")
            failed += 1
        else:
            print(f"[PASS] {case_id}")
            passed += 1
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} total")
    print("=" * 80)
    
    return failed == 0

if __name__ == "__main__":
    success = run_gold_tests()
    sys.exit(0 if success else 1)
