import json
import os
from typing import List, Set

class OntologyFilter:
    def __init__(self):
        ontology_path = os.path.join(os.path.dirname(__file__), "indian_legal_ontology.json")
        with open(ontology_path, 'r', encoding='utf-8') as f:
            self.ontology = json.load(f)
        self.acts = {act['act_id']: act for act in self.ontology['acts']}
        self.domain_rules = self.ontology['domain_rules']
    
    def get_allowed_act_ids(self, domain: str) -> Set[str]:
        """Get allowed act_ids for a domain"""
        if domain not in self.domain_rules:
            return set()
        
        rule = self.domain_rules[domain]
        allowed = set(rule.get('primary_acts', []))
        allowed.update(rule.get('procedural_acts', []))
        return allowed
    
    def normalize_act_id(self, act_id: str) -> str:
        """Normalize act_id to match ontology keys"""
        act_id = act_id.lower().strip()
        
        if act_id.startswith('in_'):
            act_id = act_id[3:]
        
        if act_id in self.acts:
            return act_id
        
        mappings = {
            'bns': 'bns_sections',
            'ipc': 'ipc_sections',
            'crpc': 'crpc_sections',
            'bnss': 'bnss_sections',
            'it_act': 'it_act_2000',
            'uapa': 'uapa_1967',
            'hindu_marriage': 'hindu_marriage_act',
            'special_marriage': 'special_marriage_act',
            'domestic_violence': 'domestic_violence_act',
            'dowry_prohibition': 'dowry_prohibition_act',
            'consumer_protection': 'consumer_protection_act',
            'labour': 'labour_employment_laws',
            'property': 'property_real_estate_laws',
            'motor_vehicles': 'motor_vehicles_act',
            'farmers_protection': 'farmers_protection_act',
            'cpc': 'cpc_sections',
            'evidence': 'indian_evidence_act'
        }
        
        for key, value in mappings.items():
            if key in act_id:
                return value
        
        return act_id
