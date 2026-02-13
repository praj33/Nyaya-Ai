import json
import os
from typing import Dict, List, Any, Optional

class AddonSubtypeResolver:
    def __init__(self):
        addon_path = os.path.join(os.path.dirname(__file__), "offense_subtypes_addon.json")
        with open(addon_path, 'r', encoding='utf-8') as f:
            self.addon_subtypes = json.load(f)
        
        # Load ontology offense subtypes
        ontology_path = os.path.join(os.path.dirname(__file__), "..", "ontology", "offense_subtypes.json")
        if os.path.exists(ontology_path):
            with open(ontology_path, 'r', encoding='utf-8') as f:
                ontology_subtypes = json.load(f)
                self.addon_subtypes.update(ontology_subtypes)
        
        # Statute completeness overlay mapping
        self.statute_overlay = {
            "Bharatiya Nyaya Sanhita": {"year": 2023},
            "Indian Penal Code": {"year": 1860},
            "Information Technology Act": {"year": 2000},
            "Minimum Wages Act": {"year": 1948},
            "Immoral Traffic (Prevention) Act": {"year": 1956},
            "Child and Adolescent Labour (Prohibition and Regulation) Act": {"year": 1986},
            "Maintenance and Welfare of Parents and Senior Citizens Act": {"year": 2007},
            "Transplantation of Human Organs and Tissues Act": {"year": 1994},
            "Prohibition of Child Marriage Act": {"year": 2006},
            "Dowry Prohibition Act": {"year": 1961},
            "Protection of Women from Domestic Violence Act": {"year": 2005},
            "Sexual Harassment of Women at Workplace Act": {"year": 2013},
            "Hindu Marriage Act": {"year": 1955},
            "Special Marriage Act": {"year": 1954},
            "Protection of Children from Sexual Offences Act": {"year": 2012}
        }
    
    def detect_addon_subtype(self, query: str) -> Optional[str]:
        """Detect addon offense subtype from query with exclude/require logic"""
        query_lower = query.lower()
        
        for subtype_name, subtype_data in self.addon_subtypes.items():
            keywords = subtype_data.get('keywords', [])
            exclude_keywords = subtype_data.get('exclude_keywords', [])
            require_keywords = subtype_data.get('require_keywords', [])
            
            # Check if any keyword matches
            if not any(kw in query_lower for kw in keywords):
                continue
            
            # Check exclude keywords
            if any(ex_kw in query_lower for ex_kw in exclude_keywords):
                continue
            
            # Check require keywords (if specified, at least one must be present)
            if require_keywords and not any(req_kw in query_lower for req_kw in require_keywords):
                continue
            
            return subtype_name
        
        return None
    
    def _complete_statute_metadata(self, statute: Dict[str, Any]) -> Dict[str, Any]:
        """Complete missing statute metadata using overlay mapping"""
        completed = statute.copy()
        act_name = statute.get('act', '')
        
        if act_name in self.statute_overlay:
            overlay_data = self.statute_overlay[act_name]
            if 'year' not in completed or not completed['year']:
                completed['year'] = overlay_data['year']
        
        return completed
    
    def enhance_response(self, base_response: Dict[str, Any], query: str, confidence: Dict[str, float] = None) -> Dict[str, Any]:
        """Enhance response with addon subtypes if base resolver has low confidence or empty results"""
        
        # Check if we should apply addon logic
        should_apply = False
        
        # Apply if no statutes found
        if not base_response.get('statutes', []):
            should_apply = True
        
        # Apply if confidence is low
        if confidence and confidence.get('statute_match', 1.0) < 0.5:
            should_apply = True
        
        if not should_apply:
            return base_response
        
        # Detect addon subtype
        addon_subtype = self.detect_addon_subtype(query)
        if not addon_subtype:
            return base_response
        
        addon_data = self.addon_subtypes[addon_subtype]
        
        # Append addon statutes with completed metadata
        addon_statutes = []
        for statute in addon_data.get('statutes', []):
            completed_statute = self._complete_statute_metadata(statute)
            addon_statutes.append({
                "act": completed_statute["act"],
                "section": completed_statute["section"],
                "title": completed_statute["title"],
                "year": completed_statute.get("year")
            })
        
        if 'statutes' not in base_response:
            base_response['statutes'] = []
        base_response['statutes'].extend(addon_statutes)
        
        # Override domains
        base_response['domains'] = addon_data.get('domains', ['criminal'])
        
        # Set enforcement decision if not already set
        if 'enforcement_decision' not in base_response:
            base_response['enforcement_decision'] = addon_data.get('enforcement_decision', 'ALLOW')
        
        # Mark as addon enhanced
        base_response['addon_enhanced'] = True
        base_response['addon_subtype'] = addon_subtype
        
        return base_response