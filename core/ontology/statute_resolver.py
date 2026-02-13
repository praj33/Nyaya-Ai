import json
import os
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

@dataclass
class QualifiedStatute:
    act: str
    year: int
    section: str
    title: str
    act_id: str
    abbreviation: str
    domain: List[str]
    priority: int = 1

class StatuteResolver:
    def __init__(self, ontology_path: str = None, use_faiss: bool = True):
        if ontology_path is None:
            ontology_path = os.path.join(
                os.path.dirname(__file__),
                "indian_legal_ontology.json"
            )
        
        with open(ontology_path, 'r', encoding='utf-8') as f:
            self.ontology = json.load(f)
        
        self.acts = {act['act_id']: act for act in self.ontology['acts']}
        self.domain_rules = self.ontology['domain_rules']
        self.auto_inclusion_rules = self.ontology['auto_inclusion_rules']
        self.offense_categories = self.ontology.get('offense_categories', {})
        
        # Load offense subtypes
        subtypes_path = os.path.join(os.path.dirname(__file__), "offense_subtypes.json")
        try:
            with open(subtypes_path, 'r', encoding='utf-8') as f:
                self.offense_subtypes = json.load(f)
        except:
            self.offense_subtypes = {}
        
        # Load actual sections from database
        from data_bridge.loader import JSONLoader
        loader = JSONLoader("db")
        self.sections, self.acts_db, self.cases = loader.load_and_normalize_directory()
        pass
        
        # Initialize FAISS search
        self.use_faiss = use_faiss
        self.faiss_search = None
        if use_faiss:
            try:
                from core.vector.faiss_search import FAISSSearch
                self.faiss_search = FAISSSearch()
                self.faiss_search.load_indexes()
                pass
            except Exception as e:
                pass
                self.faiss_search = None
    
    def detect_offense_subtype(self, query: str) -> Optional[str]:
        """Detect offense subtype from query"""
        query_lower = query.lower()
        pass
        
        # Check child_sexual_offense first (highest priority)
        if "child_sexual_offense" in self.offense_subtypes:
            child_data = self.offense_subtypes["child_sexual_offense"]
            keywords = child_data.get('keywords', [])
            if any(kw in query_lower for kw in keywords):
                pass
                return "child_sexual_offense"
        
        # Check authority_assault second (requires both authority and violence)
        if "authority_assault" in self.offense_subtypes:
            authority_data = self.offense_subtypes["authority_assault"]
            keywords = authority_data.get('keywords', [])
            trigger_verbs = authority_data.get('trigger_verbs', [])
            
            has_authority = any(kw in query_lower for kw in keywords)
            has_violence = any(verb in query_lower for verb in trigger_verbs)
            if has_authority and has_violence:
                pass
                return "authority_assault"
        
        # Check other subtypes
        for subtype_name, subtype_data in self.offense_subtypes.items():
            if subtype_name in ["child_sexual_offense", "authority_assault"]:
                continue  # Already checked above
                
            keywords = subtype_data.get('keywords', [])
            exclude_keywords = subtype_data.get('exclude_keywords', [])
            require_keywords = subtype_data.get('require_keywords', [])
            
            if exclude_keywords and any(kw in query_lower for kw in exclude_keywords):
                continue
            
            if require_keywords and not any(kw in query_lower for kw in require_keywords):
                continue
            
            if any(kw in query_lower for kw in keywords):
                pass
                return subtype_name
        
        pass
        return None
    
    def detect_offense_category(self, query: str) -> Optional[Dict[str, Any]]:
        """Detect if query matches a specific offense category"""
        query_lower = query.lower()
        
        for category_name, category_data in self.offense_categories.items():
            keywords = category_data.get('keywords', [])
            exclude_keywords = category_data.get('exclude_keywords', [])
            require_keywords = category_data.get('require_keywords', [])
            
            # Check if any exclude keyword is present
            if any(keyword in query_lower for keyword in exclude_keywords):
                continue
            
            # For categories with require_keywords, at least one must be present
            if require_keywords:
                if not any(keyword in query_lower for keyword in require_keywords):
                    continue
            
            # Check if any keyword matches
            if any(keyword in query_lower for keyword in keywords):
                return category_data
        
        return None
    
    def get_relevant_acts(self, query: str, domains: List[str], jurisdiction: str = "IN", jurisdiction_year: int = None) -> List[str]:
        """Get list of relevant act_ids based on query, domains, and jurisdiction with penal code exclusivity"""
        if jurisdiction != "IN":
            return []
        
        # Determine jurisdiction year (default to current year 2024+)
        if jurisdiction_year is None:
            from datetime import datetime
            jurisdiction_year = datetime.now().year
        
        relevant_acts = set()
        query_lower = query.lower()
        
        # Check offense subtype first (higher priority)
        subtype = self.detect_offense_subtype(query)
        pass
        if subtype and subtype in self.offense_subtypes:
            subtype_data = self.offense_subtypes[subtype]
            pass
            
            # For child_sexual_offense, force criminal domain
            if subtype == "child_sexual_offense":
                domains = ["criminal"]
            
            # For authority_assault, force criminal domain and block family
            if subtype == "authority_assault":
                domains = ["criminal"]
            
            # For gang_rape, force criminal domain
            if subtype == "gang_rape":
                domains = ["criminal"]
            
            for statute in subtype_data.get('statutes', []):
                act_name = statute['act']
                pass
                for act_id, act_meta in self.acts.items():
                    if act_meta['name'] == act_name:
                        pass
                        relevant_acts.add(act_id)
                        break
                else:
                    pass
            pass
            relevant_acts = self._apply_penal_code_exclusivity(relevant_acts, jurisdiction_year)
            pass
            return self._sort_by_priority(list(relevant_acts))
        
        # Check offense categories
        offense_category = self.detect_offense_category(query)
        if offense_category:
            # Add primary statutes
            for statute_group in offense_category.get('primary_statutes', []):
                relevant_acts.add(statute_group['act_id'])
            # Add secondary statutes
            for statute_group in offense_category.get('secondary_statutes', []):
                relevant_acts.add(statute_group['act_id'])
            
            # Apply penal code exclusivity
            relevant_acts = self._apply_penal_code_exclusivity(relevant_acts, jurisdiction_year)
            return self._sort_by_priority(list(relevant_acts))
        
        # Auto-inclusion: terrorism
        if any(keyword in query_lower for keyword in self.auto_inclusion_rules.get('terrorism_keywords', [])):
            relevant_acts.update(self.auto_inclusion_rules['terrorism_acts'])
            domains = ['terrorism']
        
        # Get domain-specific acts
        for domain in domains:
            if domain in self.domain_rules:
                rule = self.domain_rules[domain]
                relevant_acts.update(rule['primary_acts'])
                relevant_acts.update(rule.get('procedural_acts', []))
        
        # Apply penal code exclusivity
        relevant_acts = self._apply_penal_code_exclusivity(relevant_acts, jurisdiction_year)
        
        # Filter by active status
        active_acts = [
            act_id for act_id in relevant_acts
            if self.acts.get(act_id, {}).get('active', True)
        ]
        
        return self._sort_by_priority(active_acts)
    
    def _apply_penal_code_exclusivity(self, act_ids: Set[str], jurisdiction_year: int) -> Set[str]:
        """Apply penal code exclusivity rule: BNS for 2024+, IPC for pre-2024"""
        result = set(act_ids)
        
        if jurisdiction_year >= 2024:
            # Use BNS, block IPC
            if 'ipc_sections' in result:
                result.remove('ipc_sections')
            if 'crpc_sections' in result:
                result.remove('crpc_sections')
        else:
            # Use IPC, block BNS
            if 'bns_sections' in result:
                result.remove('bns_sections')
            if 'bnss_sections' in result:
                result.remove('bnss_sections')
        
        return result
    
    def _sort_by_priority(self, act_ids: List[str]) -> List[str]:
        """Sort acts by priority"""
        return sorted(
            act_ids,
            key=lambda x: self.acts.get(x, {}).get('priority', 99)
        )
    
    def should_exclude_section(self, section_act_id: str, domains: List[str]) -> bool:
        """Check if a section should be excluded based on domain rules"""
        return False
    
    def qualify_section(self, section_number: str, section_text: str, act_id: str) -> Optional[QualifiedStatute]:
        """Convert raw section to qualified statute format"""
        act = self.acts.get(act_id)
        if not act:
            return None
        
        return QualifiedStatute(
            act=act['name'],
            year=act['year'],
            section=section_number,
            title=section_text[:100] if len(section_text) > 100 else section_text,
            act_id=act_id,
            abbreviation=act['abbreviation'],
            domain=act['domain'],
            priority=act.get('priority', 1)
        )
    
    def filter_sections(self, sections: List[Any], domains: List[str], query: str, jurisdiction_year: int = None) -> List[QualifiedStatute]:
        """Filter and qualify sections based on ontology rules with FAISS semantic search"""
        
        # Try FAISS semantic search first
        if self.faiss_search:
            faiss_results = self._filter_sections_faiss(sections, domains, query, jurisdiction_year)
            if faiss_results:
                pass
                return faiss_results
            else:
                pass
        
        # Fallback to keyword-based filtering
        return self._filter_sections_keyword(sections, domains, query, jurisdiction_year)
    
    def _filter_sections_faiss(self, sections: List[Any], domains: List[str], query: str, jurisdiction_year: int = None) -> List[QualifiedStatute]:
        """Filter sections using FAISS semantic search"""
        relevant_act_ids = set(self.get_relevant_acts(query, domains, jurisdiction_year=jurisdiction_year))
        pass
        
        # Search FAISS index
        faiss_results = self.faiss_search.search_statutes(query, k=20)
        pass
        
        # Match FAISS results with actual sections
        qualified = []
        seen = set()
        
        for meta, score in faiss_results:
            normalized_act_id = self._normalize_act_id(meta['act'])
            pass
            
            # Apply domain filtering
            if relevant_act_ids and normalized_act_id not in relevant_act_ids:
                pass
                continue
            
            qualified_statute = self.qualify_section(
                meta['section'],
                meta['text'],
                normalized_act_id
            )
            
            if qualified_statute:
                key = f"{qualified_statute.act}_{qualified_statute.section}"
                if key not in seen:
                    seen.add(key)
                    qualified_statute.priority = int(score * 100)
                    qualified.append(qualified_statute)
        
        # Sort by priority
        qualified.sort(key=lambda x: (
            x.priority,
            0 if 'criminal' in x.domain else 1,
            x.act_id
        ))
        
        pass
        return qualified[:10]
    
    def _filter_sections_keyword(self, sections: List[Any], domains: List[str], query: str, jurisdiction_year: int = None) -> List[QualifiedStatute]:
        """Filter and qualify sections based on ontology rules (keyword fallback)"""
        relevant_act_ids = set(self.get_relevant_acts(query, domains, jurisdiction_year=jurisdiction_year))
        pass
        qualified = []
        seen = set()
        
        # Check for offense category to get specific sections
        offense_category = self.detect_offense_category(query)
        priority_sections = set()
        
        if offense_category:
            for statute_group in offense_category.get('primary_statutes', []):
                for section in statute_group.get('sections', []):
                    priority_sections.add(f"{statute_group['act_id']}_{section}")
        
        # Filter sections by relevant acts and query keywords
        query_lower = query.lower()
        for section in sections:
            act_id = section.act_id.lower()
            normalized_act_id = self._normalize_act_id(act_id)
            
            if relevant_act_ids and normalized_act_id not in relevant_act_ids:
                continue
            
            # Check if section text matches query keywords
            section_text = section.text.lower()
            query_words = query_lower.split()
            
            # Score based on keyword matches
            matches = sum(1 for word in query_words if len(word) > 3 and word in section_text)
            if matches == 0:
                continue
            
            qualified_statute = self.qualify_section(
                section.section_number,
                section.text,
                normalized_act_id
            )
            
            if qualified_statute:
                key = f"{qualified_statute.act}_{qualified_statute.section}"
                if key not in seen:
                    seen.add(key)
                    qualified_statute.priority = matches
                    qualified.append(qualified_statute)
        
        # Sort by priority (more matches = higher priority)
        qualified.sort(key=lambda x: -x.priority)
        
        pass
        return qualified[:10]
    
    def _normalize_act_id(self, act_id: str) -> str:
        """Normalize act_id to match ontology keys"""
        act_id = act_id.lower().strip()
        
        # Remove IN_ prefix if present
        if act_id.startswith('in_'):
            act_id = act_id[3:]
        
        if act_id in self.acts:
            return act_id
        
        # Check if it's an act name that needs to be mapped to act_id
        for ontology_act_id, act_meta in self.acts.items():
            if act_meta['name'].lower() == act_id:
                return ontology_act_id
        
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
    
    def resolve_query(self, query: str, domains: List[str] = None, jurisdiction: str = "IN", jurisdiction_year: int = None) -> Dict[str, Any]:
        """Main entry point for resolving a query to statutes"""
        if domains is None:
            domains = ["criminal"]  # Default domain
        
        # Get relevant acts
        relevant_acts = self.get_relevant_acts(query, domains, jurisdiction, jurisdiction_year)
        
        # Load actual sections from database
        from data_bridge.loader import JSONLoader
        loader = JSONLoader("db")
        sections, acts, cases = loader.load_and_normalize_directory()
        
        # Filter sections
        qualified_statutes = self.filter_sections(sections, domains, query, jurisdiction_year)
        
        return {
            'statutes': [{
                'act': s.act,
                'year': s.year,
                'section': s.section,
                'title': s.title,
                'abbreviation': s.abbreviation
            } for s in qualified_statutes],
            'domains': domains,
            'confidence': 0.8
        }
