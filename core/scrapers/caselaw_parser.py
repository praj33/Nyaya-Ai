import re
from typing import Dict

class CaselawParser:
    def parse(self, raw_judgment: Dict) -> Dict:
        case_title = raw_judgment.get('case_title', 'Unknown Case')
        court = raw_judgment.get('court', 'Supreme Court of India')
        year = raw_judgment.get('year', 2025)
        citation = raw_judgment.get('citation', '')
        judgment_text = raw_judgment.get('judgment_text', '')
        url = raw_judgment.get('url', '')
        
        principle = self._extract_principle(judgment_text)
        domain = self._detect_domain(judgment_text)
        
        return {
            'title': case_title,
            'court': court,
            'year': year,
            'citation': citation,
            'jurisdiction': 'IN',
            'domain': domain,
            'principle': principle,
            'full_text': judgment_text,
            'source': 'scraped',
            'url': url
        }
    
    def _extract_principle(self, text: str) -> str:
        sentences = text.split('.')
        if len(sentences) > 0:
            return sentences[0][:200]
        return text[:200]
    
    def _detect_domain(self, text: str) -> str:
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in ['criminal', 'murder', 'theft', 'robbery']):
            return 'criminal'
        elif any(kw in text_lower for kw in ['divorce', 'marriage', 'custody', 'maintenance']):
            return 'family'
        elif any(kw in text_lower for kw in ['contract', 'property', 'civil']):
            return 'civil'
        
        return 'unknown'
    
    def generate_case_id(self, judgment: Dict) -> str:
        title = judgment.get('title', 'case')
        year = judgment.get('year', 2025)
        
        clean_title = re.sub(r'[^a-zA-Z0-9]', '_', title.lower())[:30]
        return f"{year}_{clean_title}"
