"""
Jurisdiction Detector - Automatically infers jurisdiction from user queries
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple
import re


@dataclass
class JurisdictionResult:
    """Result of jurisdiction detection"""
    jurisdiction: str
    confidence: float


class JurisdictionDetector:
    """Detects jurisdiction from user query using keyword heuristics"""
    
    # Jurisdiction indicators with confidence weights
    JURISDICTION_KEYWORDS = {
        'IN': {
            # Legal acts and codes
            'ipc': 1.0, 'bns': 1.0, 'crpc': 1.0, 'bnss': 1.0,
            'bharatiya nyaya sanhita': 1.0, 'indian penal code': 1.0,
            'code of criminal procedure': 1.0,
            
            # Indian-specific legal terms
            'fir': 0.9, 'chargesheet': 0.9, 'cognizable': 0.9, 'non-bailable': 0.9,
            'magistrate': 0.8, 'high court': 0.7, 'supreme court': 0.7,
            'police station': 0.7, 'thana': 0.9,
            
            # Indian acts
            'uapa': 1.0, 'pocso': 1.0, 'dowry prohibition': 0.95,
            'domestic violence act': 0.9, 'hindu marriage act': 0.95,
            'special marriage act': 0.95, 'it act': 0.8,
            
            # Indian legal concepts
            'section 498a': 1.0, 'section 420': 1.0, 'section 302': 1.0,
            'anticipatory bail': 0.9, 'quash': 0.8,
            
            # Geographic indicators
            'india': 0.9, 'indian': 0.8, 'delhi': 0.7, 'mumbai': 0.7,
            'bangalore': 0.7, 'chennai': 0.7, 'kolkata': 0.7, 'hyderabad': 0.7,
            
            # Currency
            'rupees': 0.6, 'inr': 0.7, 'lakh': 0.8, 'crore': 0.8,
        }
    }
    
    # Default jurisdiction if no strong indicators
    DEFAULT_JURISDICTION = 'IN'
    DEFAULT_CONFIDENCE = 0.5
    
    # Confidence threshold for detection
    MIN_CONFIDENCE = 0.3
    
    def __init__(self):
        """Initialize detector with compiled patterns"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching"""
        self.patterns: Dict[str, List[Tuple[re.Pattern, float]]] = {}
        
        for jurisdiction, keywords in self.JURISDICTION_KEYWORDS.items():
            self.patterns[jurisdiction] = [
                (re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE), weight)
                for keyword, weight in keywords.items()
            ]
    
    def detect(self, query: str, user_hint: str = None) -> JurisdictionResult:
        """
        Detect jurisdiction from query
        
        Args:
            query: User's legal query
            user_hint: Optional jurisdiction hint from user (takes precedence)
        
        Returns:
            JurisdictionResult with jurisdiction code and confidence
        """
        # User hint takes absolute precedence
        if user_hint:
            return JurisdictionResult(
                jurisdiction=user_hint.upper(),
                confidence=1.0
            )
        
        # Calculate scores for each jurisdiction
        scores = self._calculate_scores(query)
        
        if not scores:
            # No indicators found, return default
            return JurisdictionResult(
                jurisdiction=self.DEFAULT_JURISDICTION,
                confidence=self.DEFAULT_CONFIDENCE
            )
        
        # Get highest scoring jurisdiction
        best_jurisdiction = max(scores, key=scores.get)
        confidence = min(scores[best_jurisdiction], 1.0)
        
        # If confidence too low, use default
        if confidence < self.MIN_CONFIDENCE:
            return JurisdictionResult(
                jurisdiction=self.DEFAULT_JURISDICTION,
                confidence=self.DEFAULT_CONFIDENCE
            )
        
        return JurisdictionResult(
            jurisdiction=best_jurisdiction,
            confidence=confidence
        )
    
    def _calculate_scores(self, query: str) -> Dict[str, float]:
        """Calculate jurisdiction scores based on keyword matches"""
        scores = {}
        
        for jurisdiction, patterns in self.patterns.items():
            score = 0.0
            matches = 0
            
            for pattern, weight in patterns:
                if pattern.search(query):
                    score += weight
                    matches += 1
            
            if matches > 0:
                # Normalize by number of matches to avoid over-counting
                # But give bonus for multiple indicators
                normalized_score = score / (1 + matches * 0.1)
                scores[jurisdiction] = normalized_score
        
        return scores
