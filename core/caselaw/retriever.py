from typing import List, Tuple
from .loader import CaseLaw
from core.ontology.ontology_filter import OntologyFilter

class CaseLawRetriever:
    def __init__(self, cases: List[CaseLaw]):
        self.cases = cases
        self.ontology_filter = OntologyFilter()
    
    def retrieve(
        self,
        query: str,
        domain: str,
        jurisdiction: str = "IN",
        top_k: int = 3
    ) -> List[CaseLaw]:
        """Retrieve top-K relevant cases based on keyword matching with domain filtering"""
        
        # Filter by jurisdiction and domain - STRICT MATCH
        filtered = [
            case for case in self.cases
            if case.jurisdiction == jurisdiction and case.domain == domain
        ]
        
        if not filtered:
            return []
        
        # Score cases based on keyword overlap
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_cases = []
        for case in filtered:
            score = 0
            
            # Check keyword matches
            for keyword in case.keywords:
                if keyword.lower() in query_lower:
                    score += 10
                
                # Check word overlap
                keyword_words = set(keyword.lower().split())
                overlap = len(query_words & keyword_words)
                score += overlap * 2
            
            # Check title matches
            title_words = set(case.title.lower().split())
            title_overlap = len(query_words & title_words)
            score += title_overlap
            
            # Check principle matches
            principle_words = set(case.principle.lower().split())
            principle_overlap = len(query_words & principle_words)
            score += principle_overlap * 0.5
            
            if score > 0:
                scored_cases.append((case, score))
        
        # Sort by score
        scored_cases.sort(key=lambda x: x[1], reverse=True)
        
        # Apply strict domain filtering - only return cases matching exact domain
        # No cross-domain leakage allowed
        filtered_cases = []
        for case, score in scored_cases:
            if case.domain == domain:
                filtered_cases.append((case, score))
        
        scored_cases = filtered_cases
        
        # Apply domain-specific keyword filtering for criminal cases
        if domain == "criminal":
            scored_cases = self._filter_criminal_cases(scored_cases, query_lower)
        
        return [case for case, score in scored_cases[:top_k]]
    
    def _filter_criminal_cases(self, scored_cases: List[Tuple[CaseLaw, float]], query_lower: str) -> List[Tuple[CaseLaw, float]]:
        """Filter criminal cases by allowed keywords"""
        allowed_keywords = [
            'accident', 'motor vehicle', 'rash driving', 'negligent driving',
            'homicide', 'assault', 'theft', 'rape'
        ]
        
        # Check if rape query
        is_rape_query = 'rape' in query_lower or 'sexual' in query_lower
        
        filtered = []
        for case, score in scored_cases:
            case_keywords_lower = [kw.lower() for kw in case.keywords]
            
            # Check if case has any allowed keyword
            has_allowed = any(allowed_kw in ' '.join(case_keywords_lower) for allowed_kw in allowed_keywords)
            
            # Special handling for rape cases
            if 'rape' in ' '.join(case_keywords_lower):
                if is_rape_query:
                    filtered.append((case, score))
            elif has_allowed:
                filtered.append((case, score))
        
        return filtered
