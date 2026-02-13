import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Import existing components
import sys
import os
sys.path.append('.')

from data_bridge.loader import JSONLoader
from data_bridge.schemas.section import Section, Jurisdiction
from events.event_types import EventType

class LegalDomain(Enum):
    CRIMINAL = "criminal"
    CIVIL = "civil"
    FAMILY = "family"
    COMMERCIAL = "commercial"
    CONSTITUTIONAL = "constitutional"

@dataclass
class LegalQuery:
    query_text: str
    jurisdiction_hint: Optional[str] = None
    domain_hint: Optional[str] = None
    trace_id: Optional[str] = None

@dataclass
class LegalAdvice:
    query: str
    jurisdiction: str
    domain: str
    relevant_sections: List[Section]
    legal_analysis: str
    procedural_steps: List[str]
    remedies: List[str]
    confidence_score: float
    trace_id: str
    timestamp: str

class IntegratedLegalAdvisor:
    def __init__(self):
        self.loader = JSONLoader("db")
        self.sections, self.acts, self.cases = self.loader.load_and_normalize_directory()
        self.enforcement_ledger = []
        
        # Create searchable index
        self.section_index = self._build_section_index()
        
        print(f"Loaded {len(self.sections)} sections, {len(self.acts)} acts, {len(self.cases)} cases")
        
    def _build_section_index(self) -> Dict[str, List[Section]]:
        """Build searchable index of sections by keywords"""
        index = {}
        for section in self.sections:
            # Index by section text keywords
            words = section.text.lower().split()
            for word in words:
                if len(word) > 3:  # Skip short words
                    if word not in index:
                        index[word] = []
                    index[word].append(section)
        return index
    
    def _detect_jurisdiction(self, query: str, hint: Optional[str] = None) -> str:
        """Detect jurisdiction from query or hint"""
        if hint:
            if hint.lower() in ['india', 'indian', 'in']:
                return 'IN'
            elif hint.lower() in ['uk', 'britain', 'england']:
                return 'UK'
            elif hint.lower() in ['uae', 'emirates', 'dubai']:
                return 'UAE'
        
        # Detect from query content
        query_lower = query.lower()
        if any(word in query_lower for word in ['india', 'indian', 'ipc', 'crpc', 'bns']):
            return 'IN'
        elif any(word in query_lower for word in ['uk', 'britain', 'england']):
            return 'UK'
        elif any(word in query_lower for word in ['uae', 'emirates', 'dubai']):
            return 'UAE'
        
        return 'IN'  # Default to India
    
    def _detect_domain(self, query: str, hint: Optional[str] = None) -> str:
        """Detect legal domain from query"""
        if hint:
            return hint.lower()
        
        query_lower = query.lower()
        if any(word in query_lower for word in ['theft', 'murder', 'assault', 'crime', 'police', 'arrest']):
            return 'criminal'
        elif any(word in query_lower for word in ['contract', 'property', 'tort', 'damages']):
            return 'civil'
        elif any(word in query_lower for word in ['marriage', 'divorce', 'custody', 'family']):
            return 'family'
        elif any(word in query_lower for word in ['company', 'business', 'commercial']):
            return 'commercial'
        
        return 'civil'  # Default
    
    def _search_relevant_sections(self, query: str, jurisdiction: str, domain: str) -> List[Section]:
        """Search for relevant legal sections"""
        relevant_sections = []
        query_lower = query.lower()
        
        # Define specific crime mappings
        crime_mappings = {
            'rape': ['375', '376', '376A', '376AB', '376B', '376C', '376D', '376DA', '376DB', '376E'],
            'murder': ['299', '300', '302', '303', '304', '307'],
            'theft': ['378', '379', '380', '381', '382'],
            'assault': ['351', '352', '353', '354', '354A', '354B', '354C', '354D'],
            'kidnapping': ['359', '360', '361', '363', '364', '365', '366', '367'],
            'dowry': ['304B', '498A'],
            'cheating': ['415', '416', '417', '418', '419', '420']
        }
        
        # Check for direct crime matches first
        matched_sections = []
        for crime, section_numbers in crime_mappings.items():
            if crime in query_lower:
                for section in self.sections:
                    if (section.jurisdiction.value == jurisdiction and 
                        section.section_number in section_numbers):
                        matched_sections.append((section, 10))  # High priority
        
        # If no direct matches, fall back to keyword search
        if not matched_sections:
            query_words = set(word.lower() for word in query.split() if len(word) > 2)
            
            for section in self.sections:
                if section.jurisdiction.value != jurisdiction:
                    continue
                    
                score = 0
                section_text = section.text.lower()
                
                # Check for query keywords in section text
                for word in query_words:
                    if word in section_text:
                        score += 3
                
                if score > 0:
                    matched_sections.append((section, score))
        
        # Sort by relevance and return top 5
        matched_sections.sort(key=lambda x: x[1], reverse=True)
        return [section for section, score in matched_sections[:5]]
    
    def _generate_legal_analysis(self, query: str, sections: List[Section], jurisdiction: str) -> str:
        """Generate legal analysis based on relevant sections"""
        if not sections:
            return "No specific legal provisions found for this query."
        
        # Add context-specific analysis for serious crimes
        query_lower = query.lower()
        if 'rape' in query_lower:
            analysis = f"Based on {jurisdiction} law for sexual offences:\n\n"
            analysis += "This is a serious criminal matter. The following legal provisions apply:\n\n"
        else:
            analysis = f"Based on {jurisdiction} law:\n\n"
        
        for i, section in enumerate(sections, 1):
            analysis += f"{i}. Section {section.section_number}: {section.text}\n"
            
            # Add punishment/remedies if available
            if hasattr(section, 'metadata') and section.metadata:
                if 'punishment' in section.metadata:
                    analysis += f"   Punishment: {section.metadata['punishment']}\n"
                if 'civil_remedies' in section.metadata:
                    analysis += f"   Remedies: {', '.join(section.metadata['civil_remedies'])}\n"
            analysis += "\n"
        
        return analysis
    
    def _generate_procedural_steps(self, sections: List[Section], domain: str) -> List[str]:
        """Generate procedural steps based on sections and domain"""
        steps = []
        
        if domain == 'criminal':
            # Check if this is a sexual offence case
            is_sexual_offence = any('375' in s.section_number or '376' in s.section_number for s in sections)
            
            if is_sexual_offence:
                steps = [
                    "Immediately report to police (FIR under Section 154 CrPC)",
                    "Medical examination and evidence collection",
                    "Police investigation under Section 173 CrPC",
                    "Charge sheet filing by prosecution",
                    "Fast-track court proceedings (mandatory under law)",
                    "In-camera trial to protect victim identity",
                    "Judgment and sentencing"
                ]
            else:
                steps = [
                    "File FIR/Police complaint",
                    "Police investigation and evidence collection",
                    "Charge sheet filing by prosecution",
                    "Court proceedings and trial",
                    "Judgment and sentencing"
                ]
        elif domain == 'civil':
            steps = [
                "Send legal notice to opposing party",
                "File civil suit in appropriate court",
                "Serve summons and pleadings",
                "Evidence presentation and arguments",
                "Court judgment and decree execution"
            ]
        elif domain == 'family':
            steps = [
                "Attempt mediation/counseling",
                "File petition in family court",
                "Mandatory mediation session",
                "Court hearings and evidence",
                "Final decree and implementation"
            ]
        
        return steps
    
    def _generate_remedies(self, sections: List[Section], domain: str) -> List[str]:
        """Generate available remedies"""
        remedies = []
        
        # Check if this is a sexual offence case
        is_sexual_offence = any('375' in s.section_number or '376' in s.section_number for s in sections)
        
        if is_sexual_offence:
            remedies = [
                "Criminal prosecution with rigorous imprisonment (minimum 7 years, may extend to life)",
                "Compensation under Section 357A CrPC",
                "Free legal aid under Legal Services Authorities Act",
                "Protection under Witness Protection Scheme",
                "Medical treatment at government expense"
            ]
        else:
            for section in sections:
                if hasattr(section, 'metadata') and section.metadata:
                    if 'civil_remedies' in section.metadata:
                        remedies.extend(section.metadata['civil_remedies'])
                    if 'punishment' in section.metadata:
                        remedies.append(f"Criminal: {section.metadata['punishment']}")
            
            if not remedies:
                if domain == 'criminal':
                    remedies = ["Criminal prosecution", "Imprisonment/fine as per law"]
                elif domain == 'civil':
                    remedies = ["Monetary damages", "Specific performance", "Injunction"]
        
        return remedies
    
    def _log_enforcement_event(self, event_type: str, trace_id: str, details: Dict[str, Any]):
        """Log enforcement event to ledger"""
        prev_hash = self.enforcement_ledger[-1]['hash'] if self.enforcement_ledger else "GENESIS"
        
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "trace_id": trace_id,
            "details": details,
            "prev_hash": prev_hash
        }
        
        # Calculate hash
        event_str = json.dumps(event, sort_keys=True)
        event["hash"] = hashlib.sha256(event_str.encode()).hexdigest()
        
        self.enforcement_ledger.append(event)
    
    def provide_legal_advice(self, legal_query: LegalQuery) -> LegalAdvice:
        """Main method to provide comprehensive legal advice"""
        trace_id = legal_query.trace_id or f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Log query received
        self._log_enforcement_event("query_received", trace_id, {
            "query": legal_query.query_text,
            "jurisdiction_hint": legal_query.jurisdiction_hint,
            "domain_hint": legal_query.domain_hint
        })
        
        # Detect jurisdiction and domain
        jurisdiction = self._detect_jurisdiction(legal_query.query_text, legal_query.jurisdiction_hint)
        domain = self._detect_domain(legal_query.query_text, legal_query.domain_hint)
        
        # Log classification
        self._log_enforcement_event("jurisdiction_resolved", trace_id, {
            "jurisdiction": jurisdiction,
            "domain": domain
        })
        
        # Search relevant sections
        relevant_sections = self._search_relevant_sections(legal_query.query_text, jurisdiction, domain)
        
        # Generate analysis
        legal_analysis = self._generate_legal_analysis(legal_query.query_text, relevant_sections, jurisdiction)
        procedural_steps = self._generate_procedural_steps(relevant_sections, domain)
        remedies = self._generate_remedies(relevant_sections, domain)
        
        # Calculate confidence score
        confidence_score = min(0.9, len(relevant_sections) * 0.2) if relevant_sections else 0.1
        
        # Log completion
        self._log_enforcement_event("advice_generated", trace_id, {
            "sections_found": len(relevant_sections),
            "confidence_score": confidence_score
        })
        
        return LegalAdvice(
            query=legal_query.query_text,
            jurisdiction=jurisdiction,
            domain=domain,
            relevant_sections=relevant_sections,
            legal_analysis=legal_analysis,
            procedural_steps=procedural_steps,
            remedies=remedies,
            confidence_score=confidence_score,
            trace_id=trace_id,
            timestamp=datetime.now().isoformat()
        )
    
    def save_enforcement_ledger(self, filename: str = "legal_advice_ledger.json"):
        """Save enforcement ledger to file"""
        with open(filename, 'w') as f:
            json.dump(self.enforcement_ledger, f, indent=2)

def main():
    """Demo the integrated legal advisor"""
    advisor = IntegratedLegalAdvisor()
    
    # Test queries
    test_queries = [
        LegalQuery("What is the punishment for theft in India?", "India", "criminal"),
        LegalQuery("How to file for divorce in UK?", "UK", "family"),
        LegalQuery("What are the requirements for company formation in UAE?", "UAE", "commercial"),
        LegalQuery("Can I get compensation for medical negligence?", "India", "civil")
    ]
    
    print("=== NYAYA AI INTEGRATED LEGAL ADVISOR ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query.query_text}")
        print("-" * 60)
        
        advice = advisor.provide_legal_advice(query)
        
        print(f"Jurisdiction: {advice.jurisdiction}")
        print(f"Domain: {advice.domain}")
        print(f"Confidence: {advice.confidence_score:.2f}")
        print(f"Relevant Sections: {len(advice.relevant_sections)}")
        
        print(f"\nLegal Analysis:")
        print(advice.legal_analysis[:300] + "..." if len(advice.legal_analysis) > 300 else advice.legal_analysis)
        
        print(f"\nProcedural Steps:")
        for step in advice.procedural_steps[:3]:
            print(f"  • {step}")
        
        print(f"\nAvailable Remedies:")
        for remedy in advice.remedies[:3]:
            print(f"  • {remedy}")
        
        print(f"\nTrace ID: {advice.trace_id}")
        print("=" * 60 + "\n")
    
    # Save enforcement ledger
    advisor.save_enforcement_ledger()
    print(f"Enforcement ledger saved with {len(advisor.enforcement_ledger)} events")

if __name__ == "__main__":
    main()