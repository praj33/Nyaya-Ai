import pytest
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.ontology.statute_resolver import StatuteResolver

class TestGoldCases:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.resolver = StatuteResolver(use_faiss=False)
        self.gold_cases_dir = Path(__file__).parent / "gold_cases"
    
    def load_gold_cases(self):
        """Load all gold case JSON files"""
        cases = []
        for json_file in self.gold_cases_dir.glob("*.json"):
            if json_file.name == "schema.json":
                continue
            with open(json_file, 'r', encoding='utf-8') as f:
                file_cases = json.load(f)
                cases.extend(file_cases)
        return cases
    
    def test_gold_cases(self):
        """Test all gold cases"""
        cases = self.load_gold_cases()
        failures = []
        
        for case in cases:
            case_id = case['id']
            query = case['query']
            expected_domains = set(case['expected_domains'])
            must_include = case['must_include_statutes']
            must_not_include = case.get('must_not_include_statutes', [])
            
            # Detect subtype or category
            subtype = self.resolver.detect_offense_subtype(query)
            category = self.resolver.detect_offense_category(query)
            
            # Get domains
            if subtype and subtype in self.resolver.offense_subtypes:
                detected_domains = set(self.resolver.offense_subtypes[subtype]['domains'])
            elif category:
                detected_domains = set(category.get('domains', []))
            else:
                detected_domains = set()
            
            # Get statutes
            acts = self.resolver.get_relevant_acts(query, list(detected_domains), jurisdiction_year=2024)
            
            statutes = []
            if subtype and subtype in self.resolver.offense_subtypes:
                statutes = self.resolver.offense_subtypes[subtype]['statutes']
            elif category:
                for sg in category.get('primary_statutes', []):
                    act_id = sg['act_id']
                    if act_id in acts:
                        act_name = self.resolver.acts[act_id]['name']
                        for section in sg['sections']:
                            statutes.append({'act': act_name, 'section': section})
            
            # Validate domains
            if not expected_domains.issubset(detected_domains):
                failures.append({
                    'case_id': case_id,
                    'query': query,
                    'error': f"Domain mismatch. Expected {expected_domains}, got {detected_domains}"
                })
                continue
            
            # Validate must_include
            for required in must_include:
                found = any(
                    s['act'] == required['act'] and s['section'] == required['section']
                    for s in statutes
                )
                if not found:
                    failures.append({
                        'case_id': case_id,
                        'query': query,
                        'error': f"Missing required statute: {required['act']} Section {required['section']}"
                    })
            
            # Validate must_not_include
            for forbidden in must_not_include:
                found = any(
                    s['act'] == forbidden['act'] and s['section'] == forbidden['section']
                    for s in statutes
                )
                if found:
                    failures.append({
                        'case_id': case_id,
                        'query': query,
                        'error': f"Forbidden statute present: {forbidden['act']} Section {forbidden['section']}"
                    })
        
        if failures:
            error_msg = "\n".join([
                f"[{f['case_id']}] {f['query']}: {f['error']}"
                for f in failures
            ])
            pytest.fail(f"Gold cases failed:\n{error_msg}")
    
    def test_dowry_demand_vs_death(self):
        """Specific test for dowry demand vs death separation"""
        # Dowry demand
        query1 = "my husband is demanding dowry"
        subtype1 = self.resolver.detect_offense_subtype(query1)
        assert subtype1 == "dowry_demand"
        
        statutes1 = self.resolver.offense_subtypes[subtype1]['statutes']
        has_85 = any(s['section'] == '85' and 'Nyaya Sanhita' in s['act'] for s in statutes1)
        has_80 = any(s['section'] == '80' and 'Nyaya Sanhita' in s['act'] for s in statutes1)
        
        assert has_85, "BNS 85 must be present in dowry demand"
        assert not has_80, "BNS 80 must not be present in dowry demand"
        
        # Dowry death
        query2 = "my wife died due to dowry"
        subtype2 = self.resolver.detect_offense_subtype(query2)
        assert subtype2 == "dowry_death"
        
        statutes2 = self.resolver.offense_subtypes[subtype2]['statutes']
        has_85 = any(s['section'] == '85' and 'Nyaya Sanhita' in s['act'] for s in statutes2)
        has_80 = any(s['section'] == '80' and 'Nyaya Sanhita' in s['act'] for s in statutes2)
        
        assert has_80, "BNS 80 must be present in dowry death"
        assert not has_85, "BNS 85 must not be present in dowry death"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
