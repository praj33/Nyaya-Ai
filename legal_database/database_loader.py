"""Legal database loader for comprehensive legal data integration."""
import json
import os
from typing import Dict, Any, List, Optional

class LegalDatabaseLoader:
    """Loads and provides access to comprehensive legal databases."""
    
    def __init__(self, db_path: str = "db"):
        self.db_path = db_path
        self.databases = {}
        self._load_databases()
    
    def _load_databases(self):
        """Load all legal databases and domain maps."""
        db_files = {
            'indian_law': 'indian_law_dataset.json',
            'uae_law': 'uae_comprehensive_laws_reference.json',
            'uk_law': 'uk_law_dataset.json',
            'bns_sections': 'bns_sections.json',
            'uae_crimes': 'uae_crimes_and_penalties_law.json',
            'uae_personal_status': 'uae_personal_status_map.json',
            'indian_domain_map': 'indian_domain_map.json',
            'uae_domain_map': 'uae_domain_map.json',
            'uk_domain_map': 'uk_domain_map.json'
        }
        
        for key, filename in db_files.items():
            file_path = os.path.join(self.db_path, filename)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.databases[key] = json.load(f)
                except Exception:
                    pass
    
    def classify_query_domain(self, query: str, jurisdiction: str) -> Dict[str, Any]:
        """Classify query into legal domain using keyword mapping."""
        jurisdiction_key = f"{jurisdiction.lower()}_domain_map"
        domain_map = self.databases.get(jurisdiction_key, {})
        
        if not domain_map:
            return {"domain": "criminal", "confidence": 0.5, "subdomains": []}
        
        query_lower = query.lower()
        keyword_mapping = domain_map.get("keyword_mapping", {})
        domain_mapping = domain_map.get("domain_mapping", {})
        
        domain_scores = {}
        subdomain_matches = []
        
        for subdomain, keywords in keyword_mapping.items():
            matches = sum(1 for keyword in keywords if keyword.lower() in query_lower)
            if matches > 0:
                subdomain_matches.append(subdomain)
                for domain, config in domain_mapping.items():
                    if subdomain in config.get("subdomains", []):
                        domain_scores[domain] = domain_scores.get(domain, 0) + matches
        
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            confidence = min(0.9, domain_scores[best_domain] * 0.2 + 0.5)
        else:
            best_domain = domain_map.get("fallback_rules", {}).get("default_domain", "criminal")
            confidence = 0.3
        
        return {
            "domain": best_domain,
            "confidence": confidence,
            "subdomains": subdomain_matches,
            "threshold": domain_mapping.get(best_domain, {}).get("confidence_threshold", 0.7)
        }
    
    def get_legal_sections(self, query: str, jurisdiction: str, domain: str) -> List[Dict[str, Any]]:
        """Get relevant legal sections based on query and jurisdiction."""
        sections = []
        query_lower = query.lower()
        
        if jurisdiction.lower() == "india":
            indian_law = self.databases.get('indian_law', {}).get('bns_sections', {})
            for section_name, section_data in indian_law.items():
                if isinstance(section_data, dict):
                    section_text = section_data.get('offence', '') + ' ' + str(section_data.get('elements_required', []))
                    if any(word in section_text.lower() for word in query_lower.split()):
                        sections.append({
                            'section': section_data.get('section', section_name),
                            'title': section_data.get('offence', ''),
                            'punishment': section_data.get('punishment', ''),
                            'elements': section_data.get('elements_required', []),
                            'process': section_data.get('process_steps', [])
                        })
        
        elif jurisdiction.lower() == "uae":
            uae_crimes = self.databases.get('uae_crimes', {}).get('key_offences', {})
            for offense_name, offense_data in uae_crimes.items():
                if any(word in offense_name.lower() for word in query_lower.split()):
                    sections.append({
                        'offense': offense_name,
                        'penalty': offense_data if isinstance(offense_data, str) else str(offense_data),
                        'category': 'criminal'
                    })
        
        elif jurisdiction.lower() == "uk":
            uk_law = self.databases.get('uk_law', {})
            for law_type in ['criminal_law', 'civil_law']:
                if law_type in uk_law:
                    for act_name, act_data in uk_law[law_type].items():
                        if isinstance(act_data, dict):
                            for section_name, section_data in act_data.items():
                                if isinstance(section_data, dict):
                                    section_text = section_data.get('offence', '') + ' ' + section_data.get('title', '')
                                    if any(word in section_text.lower() for word in query.lower().split()):
                                        sections.append({
                                            'act': act_name,
                                            'section': section_name,
                                            'title': section_data.get('offence', section_data.get('title', '')),
                                            'punishment': section_data.get('punishment', ''),
                                            'type': law_type
                                        })
        
        return sections[:5]

legal_db = LegalDatabaseLoader()