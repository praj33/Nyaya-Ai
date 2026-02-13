from typing import List, Dict, Any, Tuple

class DowryPrecisionLayer:
    """Post-retrieval filtering and prioritization for dowry offences"""
    
    DOWRY_INDICATORS = ["dowry", "demanding dowry", "harassing for dowry", "dowry harassment", "dowry demand"]
    
    PRIORITY_ORDER = [
        ("Dowry Prohibition Act", None),
        ("Bharatiya Nyaya Sanhita", "85"),
        ("Indian Penal Code", "498A"),
        ("Protection of Women from Domestic Violence Act", None)
    ]
    
    FILTER_KEYWORDS = ["dowry", "cruelty", "husband", "relative"]
    
    def detect_dowry_query(self, query: str) -> bool:
        """Detect if query is about dowry offences"""
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in self.DOWRY_INDICATORS)
    
    def filter_and_prioritize(self, statutes: List[Dict[str, Any]], query: str) -> Tuple[List[Dict[str, Any]], bool]:
        """Filter and prioritize dowry statutes"""
        if not self.detect_dowry_query(query):
            return statutes, False
        
        # Filter: Keep only dowry-relevant statutes
        filtered = []
        for statute in statutes:
            title_lower = statute.get('title', '').lower()
            section = statute.get('section', '')
            act = statute.get('act', '')
            
            # Check if statute is dowry-relevant
            if any(kw in title_lower for kw in self.FILTER_KEYWORDS):
                filtered.append(statute)
            # Also keep if it's in priority list
            elif any(act_name in act for act_name, sec in self.PRIORITY_ORDER if sec is None or sec == section):
                filtered.append(statute)
        
        # Prioritize by defined order
        prioritized = []
        for act_name, section_num in self.PRIORITY_ORDER:
            for statute in filtered:
                if act_name in statute.get('act', ''):
                    if section_num is None or statute.get('section') == section_num:
                        if statute not in prioritized:
                            prioritized.append(statute)
        
        # Add remaining filtered statutes
        for statute in filtered:
            if statute not in prioritized:
                prioritized.append(statute)
        
        return prioritized, True
    
    def boost_confidence(self, statutes: List[Dict[str, Any]]) -> float:
        """Calculate confidence boost based on priority statute count"""
        priority_count = 0
        for statute in statutes:
            act = statute.get('act', '')
            section = statute.get('section', '')
            
            # Count priority statutes
            if "Dowry Prohibition Act" in act:
                priority_count += 1
            elif "Bharatiya Nyaya Sanhita" in act and section == "85":
                priority_count += 1
            elif "Indian Penal Code" in act and section == "498A":
                priority_count += 1
        
        return 0.95 if priority_count >= 2 else 0.8
