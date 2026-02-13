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
from procedures.loader import procedure_loader

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

class EnhancedLegalAdvisor:
    def __init__(self):
        self.loader = JSONLoader("db")
        self.sections, self.acts, self.cases = self.loader.load_and_normalize_directory()
        self.enforcement_ledger = []
        
        # Create comprehensive searchable indexes
        self.section_index = self._build_section_index()
        self.jurisdiction_sections = self._build_jurisdiction_index()
        self.crime_mappings = self._build_crime_mappings()
        
        print(f"Enhanced Legal Advisor loaded:")
        print(f"  - {len(self.sections)} sections")
        print(f"  - {len(self.acts)} acts") 
        print(f"  - {len(self.cases)} cases")
        print(f"  - {len(self.jurisdiction_sections)} jurisdictions")
        
    def _build_section_index(self) -> Dict[str, List[Section]]:
        """Build comprehensive searchable index of sections by keywords"""
        index = {}
        for section in self.sections:
            # Index by section text keywords
            words = section.text.lower().split()
            for word in words:
                if len(word) > 2:  # Include more words
                    if word not in index:
                        index[word] = []
                    index[word].append(section)
            
            # Index by section number
            if section.section_number:
                key = section.section_number.lower()
                if key not in index:
                    index[key] = []
                index[key].append(section)
                
            # Index by act_id keywords
            if section.act_id:
                act_words = section.act_id.lower().replace('_', ' ').split()
                for word in act_words:
                    if len(word) > 2:
                        if word not in index:
                            index[word] = []
                        index[word].append(section)
        
        return index
    
    def _build_jurisdiction_index(self) -> Dict[str, List[Section]]:
        """Build index by jurisdiction"""
        index = {}
        for section in self.sections:
            jurisdiction = section.jurisdiction.value
            if jurisdiction not in index:
                index[jurisdiction] = []
            index[jurisdiction].append(section)
        return index
    
    def _build_crime_mappings(self) -> Dict[str, Dict[str, List[str]]]:
        """Build comprehensive crime to section mappings for all jurisdictions"""
        mappings = {
            'IN': {
                'rape': ['63', '64', '65', '66', '375', '376', '376A', '376AB', '376B', '376C', '376D', '376DA', '376DB', '376E'],
                'murder': ['100', '101', '103', '299', '300', '302', '303', '304', '307'],
                'theft': ['303', '304', '305', '306', '307', '378', '379', '380', '381', '382'],
                'assault': ['130', '131', '132', '133', '134', '135', '136', '351', '352', '353', '354', '354A', '354B', '354C', '354D'],
                'kidnapping': ['87', '137', '138', '139', '140', '141', '142', '359', '360', '361', '363', '364', '365', '366', '367'],
                'dowry': ['80', '304B', '498A'],
                'cheating': ['318', '319', '415', '416', '417', '418', '419', '420'],
                'robbery': ['309', '310', '311', '312', '390', '391', '392', '393', '394', '395', '396', '397', '398', '399', '400'],
                'extortion': ['308', '383', '384', '385', '386', '387', '388', '389'],
                'hurt': ['114', '115', '116', '117', '118', '119', '120', '121', '122', '123', '124', '125', '319', '320', '321', '322', '323', '324', '325', '326'],
                'criminal_force': ['128', '129', '349', '350'],
                'wrongful_restraint': ['126', '127', '339', '340', '341', '342', '343', '344', '345', '346', '347', '348'],
                'defamation': ['356', '499', '500', '501', '502'],
                'criminal_intimidation': ['224', '225', '351', '503', '504', '505', '506', '507', '508'],
                'forgery': ['335', '336', '337', '338', '339', '340', '341', '342', '343', '344', '463', '464', '465', '466', '467', '468', '469', '470', '471'],
                'mischief': ['324', '325', '326', '327', '328', '425', '426', '427', '428', '429', '430', '431', '432', '433', '434', '435', '436', '437', '438', '439', '440'],
                'trespass': ['329', '330', '331', '332', '333', '334', '441', '442', '443', '444', '445', '446', '447', '448', '449', '450', '451', '452', '453', '454', '455', '456', '457', '458', '459', '460', '461', '462'],
                'abetment': ['45', '46', '47', '48', '49', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '60', '107', '108', '109', '110', '111', '112', '113', '114', '115', '116', '117', '118', '119', '120'],
                'conspiracy': ['61', '120A', '120B'],
                'sedition': ['124A', '152'],
                'suicide': ['108', '305', '306', '107', '309'],
                'abetment_suicide': ['108', '306', '107'],
                'attempt_suicide': ['309'],
                'terrorism': ['113'],
                'organised_crime': ['111', '112'],
                'trafficking': ['143', '144', '145', '146', '370', '370A', '371', '372', '373', '374']
            },
            'UK': {
                'theft': ['section_1_theft'],
                'robbery': ['section_8_robbery'],
                'burglary': ['section_9_burglary'],
                'fraud': ['section_1_fraud_by_false_representation', 'section_2_fraud_by_failure_to_disclose', 'section_3_fraud_by_abuse_of_position'],
                'assault': ['section_18_wounding_with_intent', 'section_20_malicious_wounding', 'section_39_common_assault'],
                'rape': ['section_1_rape', 'section_2_assault_by_penetration', 'section_3_sexual_assault'],
                'drugs': ['section_4_production_and_supply', 'section_5_possession'],
                'cybercrime': ['section_1_unauthorised_access', 'section_2_unauthorised_access_with_intent', 'section_3_unauthorised_modification'],
                'dangerous_driving': ['section_1_causing_death_by_dangerous_driving', 'section_2_dangerous_driving'],
                'drink_driving': ['section_4_driving_with_excess_alcohol']
            },
            'UAE': {
                'theft': ['article_391'],
                'robbery': ['article_392'],
                'assault': ['article_333'],
                'defamation': ['article_372'],
                'cybercrime': ['unauthorized_access_article_3', 'data_interference_article_4', 'cyber_fraud_article_6'],
                'drugs': ['possession_article_39', 'trafficking_article_40'],
                'drunk_driving': ['drunk_driving_article_62']
            }
        }
        return mappings
    
    def _detect_jurisdiction(self, query: str, hint: Optional[str] = None) -> str:
        """Enhanced jurisdiction detection with comprehensive keyword matching"""
        if hint:
            hint_lower = hint.lower()
            if hint_lower in ['india', 'indian', 'in', 'bharat']:
                return 'IN'
            elif hint_lower in ['uk', 'britain', 'england', 'united kingdom', 'british']:
                return 'UK'
            elif hint_lower in ['uae', 'emirates', 'dubai', 'abu dhabi', 'united arab emirates']:
                return 'UAE'
        
        # Enhanced detection from query content
        query_lower = query.lower()
        
        # India indicators
        india_keywords = ['india', 'indian', 'ipc', 'crpc', 'bns', 'bharatiya', 'nyaya', 'sanhita', 
                         'delhi', 'mumbai', 'bangalore', 'chennai', 'kolkata', 'hyderabad',
                         'supreme court of india', 'high court', 'magistrate', 'fir', 'police station']
        
        # UK indicators  
        uk_keywords = ['uk', 'britain', 'england', 'scotland', 'wales', 'london', 'manchester',
                      'crown court', 'magistrates court', 'british', 'english law', 'cps',
                      'crown prosecution service', 'solicitor', 'barrister']
        
        # UAE indicators
        uae_keywords = ['uae', 'emirates', 'dubai', 'abu dhabi', 'sharjah', 'ajman', 'ras al khaimah',
                       'fujairah', 'umm al quwain', 'federal law', 'sharia', 'dirhams', 'aed']
        
        india_score = sum(1 for keyword in india_keywords if keyword in query_lower)
        uk_score = sum(1 for keyword in uk_keywords if keyword in query_lower)
        uae_score = sum(1 for keyword in uae_keywords if keyword in query_lower)
        
        if india_score > uk_score and india_score > uae_score:
            return 'IN'
        elif uk_score > india_score and uk_score > uae_score:
            return 'UK'
        elif uae_score > india_score and uae_score > uk_score:
            return 'UAE'
        
        return 'IN'  # Default to India
    
    def _detect_domain(self, query: str, hint: Optional[str] = None) -> str:
        """Enhanced domain detection with comprehensive keyword matching"""
        if hint:
            return hint.lower()
        
        query_lower = query.lower()
        
        # Criminal law indicators
        criminal_keywords = ['theft', 'murder', 'assault', 'rape', 'robbery', 'burglary', 'fraud',
                           'kidnapping', 'extortion', 'criminal', 'crime', 'police', 'arrest',
                           'fir', 'charge', 'prosecution', 'jail', 'prison', 'bail', 'custody',
                           'investigation', 'evidence', 'witness', 'accused', 'defendant',
                           'cybercrime', 'drugs', 'trafficking', 'terrorism', 'violence', 'suicide']
        
        # Civil law indicators
        civil_keywords = ['contract', 'property', 'tort', 'damages', 'compensation', 'negligence',
                         'breach', 'liability', 'dispute', 'claim', 'suit', 'plaintiff',
                         'defendant', 'injunction', 'specific performance', 'restitution',
                         'employment', 'landlord', 'tenant', 'consumer', 'insurance']
        
        # Family law indicators
        family_keywords = ['marriage', 'divorce', 'custody', 'family', 'child', 'adoption',
                          'maintenance', 'alimony', 'dowry', 'domestic violence', 'separation',
                          'matrimonial', 'guardianship', 'inheritance', 'succession', 'will']
        
        # Commercial law indicators
        commercial_keywords = ['company', 'business', 'commercial', 'corporate', 'partnership',
                              'llc', 'limited liability', 'shares', 'shareholders', 'directors',
                              'merger', 'acquisition', 'bankruptcy', 'insolvency', 'trade',
                              'intellectual property', 'patent', 'trademark', 'copyright']
        
        criminal_score = sum(1 for keyword in criminal_keywords if keyword in query_lower)
        civil_score = sum(1 for keyword in civil_keywords if keyword in query_lower)
        family_score = sum(1 for keyword in family_keywords if keyword in query_lower)
        commercial_score = sum(1 for keyword in commercial_keywords if keyword in query_lower)
        
        scores = {
            'criminal': criminal_score,
            'civil': civil_score,
            'family': family_score,
            'commercial': commercial_score
        }
        
        max_domain = max(scores, key=scores.get)
        if scores[max_domain] > 0:
            return max_domain
        
        return 'civil'  # Default
    
    def multi_strategy_search(self, query: str, jurisdiction: str, domain: str) -> List[Section]:
        """Multi-strategy search combining enhanced legal advisor and statute retriever"""
        print("STATUTE RETRIEVER EXECUTED")
        
        # Strategy 1: Use enhanced legal advisor search
        advisor_sections = self._search_relevant_sections(query, jurisdiction, domain)
        
        # Strategy 2: Use statute retriever for additional statutes
        try:
            from core.ontology.statute_resolver import StatuteResolver
            statute_resolver = StatuteResolver()
            statute_result = statute_resolver.resolve_query(query, [domain], jurisdiction)
            
            # Convert statute results to sections
            statute_sections = []
            for statute_data in statute_result.get('statutes', []):
                # Find matching section in our database
                for section in self.sections:
                    if (section.section_number == statute_data['section'] and 
                        statute_data['act'].lower() in section.act_id.lower()):
                        statute_sections.append(section)
                        break
            
            # Merge results, prioritizing advisor sections
            all_sections = advisor_sections[:]
            for statute_section in statute_sections:
                if statute_section not in advisor_sections:
                    all_sections.append(statute_section)
            
            return all_sections[:10]  # Return top 10
            
        except Exception as e:
            print(f"Statute retriever failed: {e}")
            return advisor_sections
    
    def _search_relevant_sections(self, query: str, jurisdiction: str, domain: str) -> List[Section]:
        """Enhanced section search with multiple matching strategies"""
        relevant_sections = []
        query_lower = query.lower()
        
        # Strategy 1: Direct crime mapping using offense subtypes
        matched_sections = []
        if jurisdiction in self.crime_mappings:
            for crime, section_numbers in self.crime_mappings[jurisdiction].items():
                if crime in query_lower or any(word in query_lower for word in crime.split('_')):
                    for section in self.sections:
                        if (section.jurisdiction.value == jurisdiction and 
                            section.section_number in section_numbers):
                            matched_sections.append((section, 15))  # Highest priority
        
        # Strategy 2: Keyword matching in section text
        query_words = set(word.lower() for word in query.split() if len(word) > 2)
        for word in query_words:
            if word in self.section_index:
                for section in self.section_index[word]:
                    if section.jurisdiction.value == jurisdiction:
                        # Calculate relevance score
                        score = 0
                        section_text_lower = section.text.lower()
                        
                        # Exact word matches
                        for query_word in query_words:
                            if query_word in section_text_lower:
                                score += 5
                        
                        # Partial matches
                        for query_word in query_words:
                            if any(query_word in word for word in section_text_lower.split()):
                                score += 2
                        
                        # Domain relevance boost
                        domain_keywords = {
                            'criminal': ['offence', 'punishment', 'imprisonment', 'fine', 'criminal'],
                            'civil': ['damages', 'compensation', 'liability', 'breach', 'contract'],
                            'family': ['marriage', 'divorce', 'custody', 'family', 'matrimonial'],
                            'commercial': ['company', 'business', 'commercial', 'trade', 'corporate']
                        }
                        
                        if domain in domain_keywords:
                            for domain_word in domain_keywords[domain]:
                                if domain_word in section_text_lower:
                                    score += 3
                        
                        if score > 0:
                            matched_sections.append((section, score))
        
        # Strategy 3: Metadata matching
        for section in self.jurisdiction_sections.get(jurisdiction, []):
            if hasattr(section, 'metadata') and section.metadata:
                metadata_text = str(section.metadata).lower()
                score = 0
                for word in query_words:
                    if word in metadata_text:
                        score += 4
                
                if score > 0:
                    matched_sections.append((section, score))
        
        # Remove duplicates and sort by relevance
        unique_sections = {}
        for section, score in matched_sections:
            if section.section_id not in unique_sections:
                unique_sections[section.section_id] = (section, score)
            else:
                # Keep higher score
                if score > unique_sections[section.section_id][1]:
                    unique_sections[section.section_id] = (section, score)
        
        # Sort by relevance and return top 10
        sorted_sections = sorted(unique_sections.values(), key=lambda x: x[1], reverse=True)
        return [section for section, score in sorted_sections[:10]]
    
    def _generate_legal_analysis(self, query: str, sections: List[Section], jurisdiction: str) -> str:
        """Generate comprehensive legal analysis based on relevant sections"""
        if not sections:
            return f"No specific legal provisions found for this query in {jurisdiction} jurisdiction. Please provide more specific details or consult a legal professional."
        
        query_lower = query.lower()
        analysis = f"Legal Analysis for {jurisdiction} Jurisdiction:\n\n"
        
        # Add context-specific analysis
        if any(word in query_lower for word in ['rape', 'sexual assault', 'sexual harassment']):
            analysis += "⚠️  SERIOUS CRIMINAL MATTER - SEXUAL OFFENCE ⚠️\n"
            analysis += "This involves grave criminal charges with severe penalties. Immediate legal action required.\n\n"
        elif any(word in query_lower for word in ['murder', 'homicide', 'killing']):
            analysis += "⚠️  SERIOUS CRIMINAL MATTER - HOMICIDE ⚠️\n"
            analysis += "This involves the most serious criminal charges. Immediate legal representation essential.\n\n"
        elif any(word in query_lower for word in ['theft', 'robbery', 'burglary', 'stealing']):
            analysis += "PROPERTY CRIME MATTER\n"
            analysis += "This involves property-related criminal charges with potential imprisonment.\n\n"
        
        analysis += "Applicable Legal Provisions:\n"
        analysis += "=" * 50 + "\n\n"
        
        for i, section in enumerate(sections, 1):
            analysis += f"{i}. Section {section.section_number}"
            
            # Add act information if available
            if section.act_id:
                act_name = section.act_id.replace('_', ' ').title()
                analysis += f" ({act_name})"
            
            analysis += f":\n"
            analysis += f"   {section.text}\n"
            
            # Add punishment/remedies if available
            if hasattr(section, 'metadata') and section.metadata:
                if 'punishment' in section.metadata:
                    analysis += f"   📋 Punishment: {section.metadata['punishment']}\n"
                if 'civil_remedies' in section.metadata:
                    remedies = section.metadata['civil_remedies']
                    if isinstance(remedies, list):
                        analysis += f"   ⚖️  Remedies: {', '.join(remedies)}\n"
                    else:
                        analysis += f"   ⚖️  Remedies: {remedies}\n"
                if 'elements_required' in section.metadata:
                    elements = section.metadata['elements_required']
                    if isinstance(elements, list):
                        analysis += f"   📝 Required Elements: {', '.join(elements)}\n"
                if 'process_steps' in section.metadata:
                    steps = section.metadata['process_steps']
                    if isinstance(steps, list) and steps:
                        analysis += f"   🔄 Process: {', '.join(steps[:3])}...\n"
            
            analysis += "\n"
        
        # Add jurisdiction-specific notes
        if jurisdiction == 'IN':
            analysis += "📍 Indian Legal System Notes:\n"
            analysis += "- Cases are tried under Indian Penal Code (IPC) or Bharatiya Nyaya Sanhita (BNS)\n"
            analysis += "- Criminal cases: Police investigation → Charge sheet → Trial → Judgment\n"
            analysis += "- Civil cases: Plaint filing → Written statement → Evidence → Judgment\n"
        elif jurisdiction == 'UK':
            analysis += "📍 UK Legal System Notes:\n"
            analysis += "- Criminal cases: Police investigation → CPS charging → Court trial\n"
            analysis += "- Civil cases: County Court or High Court depending on value\n"
            analysis += "- Legal aid may be available for qualifying cases\n"
        elif jurisdiction == 'UAE':
            analysis += "📍 UAE Legal System Notes:\n"
            analysis += "- Federal and local laws apply depending on emirate\n"
            analysis += "- Sharia principles influence family and personal status matters\n"
            analysis += "- Mediation often mandatory before court proceedings\n"
        
        return analysis
    
    def _generate_procedural_steps(self, sections: List[Section], domain: str, jurisdiction: str) -> List[str]:
        """Generate detailed procedural steps from procedure datasets"""
        jurisdiction_map = {'IN': 'india', 'UK': 'uk', 'UAE': 'uae'}
        country = jurisdiction_map.get(jurisdiction, 'india').lower()
        
        procedure = procedure_loader.get_procedure(country, domain.lower())
        
        if procedure and "procedure" in procedure and "steps" in procedure["procedure"]:
            steps = procedure["procedure"]["steps"]
            return [f"{step.get('title', '')}" for step in steps]
        
        return ["Consult legal counsel", "Gather evidence", "File appropriate action"]
        
        # Check for specific offense types
        is_sexual_offence = any('375' in s.section_number or '376' in s.section_number or 
                               '63' in s.section_number or '64' in s.section_number or
                               'rape' in s.section_id.lower() for s in sections)
        
        is_serious_crime = any(word in s.text.lower() for s in sections 
                              for word in ['murder', 'homicide', 'terrorism', 'trafficking'])
        
        if domain == 'criminal':
            if jurisdiction == 'IN':
                if is_sexual_offence:
                    steps = [
                        "🚨 IMMEDIATE: Report to police (FIR under Section 154 CrPC)",
                        "🏥 Medical examination and evidence collection (within 24 hours)",
                        "👮 Police investigation under Section 173 CrPC",
                        "📋 Charge sheet filing by prosecution",
                        "⚡ Fast-track court proceedings (mandatory under law)",
                        "🔒 In-camera trial to protect victim identity",
                        "⚖️  Judgment and sentencing",
                        "📞 Victim support services and compensation under Section 357A CrPC"
                    ]
                elif is_serious_crime:
                    steps = [
                        "🚨 Immediate police reporting and FIR registration",
                        "🔍 Detailed investigation and evidence collection",
                        "👨‍💼 Senior police officer supervision",
                        "📋 Charge sheet filing within 90 days",
                        "🏛️  Sessions Court trial",
                        "⚖️  Judgment and sentencing",
                        "📈 Appeal options to High Court/Supreme Court"
                    ]
                else:
                    steps = [
                        "📝 File FIR/Police complaint at nearest police station",
                        "🔍 Police investigation and evidence collection",
                        "📋 Charge sheet filing by prosecution",
                        "🏛️  Court proceedings and trial",
                        "⚖️  Judgment and sentencing"
                    ]
            
            elif jurisdiction == 'UK':
                steps = [
                    "📞 Report to police (999 for emergencies, 101 for non-emergencies)",
                    "🔍 Police investigation and evidence gathering",
                    "👨‍💼 Crown Prosecution Service (CPS) charging decision",
                    "🏛️  Magistrates' Court or Crown Court trial",
                    "⚖️  Sentencing if convicted",
                    "📈 Appeal options to Court of Appeal"
                ]
            
            elif jurisdiction == 'UAE':
                steps = [
                    "📞 Report to police (999 emergency or local police station)",
                    "🔍 Police investigation and evidence collection",
                    "👨‍💼 Public prosecution review and charging",
                    "🏛️  Criminal court trial",
                    "⚖️  Judgment and sentencing",
                    "📈 Appeal to Court of Appeal and Cassation Court"
                ]
        
        elif domain == 'civil':
            if jurisdiction == 'IN':
                steps = [
                    "📧 Send legal notice to opposing party (mandatory)",
                    "📝 File civil suit in appropriate court with jurisdiction",
                    "📋 Serve summons and pleadings to defendant",
                    "🔄 Written statement filing by defendant",
                    "📊 Evidence presentation and arguments",
                    "⚖️  Court judgment and decree",
                    "🔨 Decree execution if required"
                ]
            
            elif jurisdiction == 'UK':
                steps = [
                    "📧 Pre-action correspondence and protocol compliance",
                    "📝 File claim in County Court or High Court",
                    "📋 Serve claim on defendant",
                    "🔄 Defence filing and case management",
                    "📊 Evidence exchange and trial",
                    "⚖️  Judgment and enforcement"
                ]
            
            elif jurisdiction == 'UAE':
                steps = [
                    "🤝 Mandatory mediation attempt (in some emirates)",
                    "📝 File civil claim in competent court",
                    "📋 Serve claim documents on defendant",
                    "🔄 Defence filing and case preparation",
                    "📊 Court hearings and evidence presentation",
                    "⚖️  Judgment and execution"
                ]
        
        elif domain == 'family':
            if jurisdiction == 'IN':
                steps = [
                    "🤝 Attempt mediation/counseling (recommended)",
                    "📝 File petition in family court",
                    "🔄 Mandatory mediation session",
                    "📋 Evidence and witness examination",
                    "⚖️  Final decree and implementation"
                ]
            
            elif jurisdiction == 'UK':
                steps = [
                    "📋 Mediation Information and Assessment Meeting (MIAM)",
                    "📝 Family Court proceedings",
                    "👶 CAFCASS involvement for children matters",
                    "🔄 First Hearing Dispute Resolution (FHDRA)",
                    "⚖️  Final hearing with judgment"
                ]
            
            elif jurisdiction == 'UAE':
                steps = [
                    "🤝 Reconciliation committee involvement",
                    "📝 Personal Status Court proceedings",
                    "🔄 Court-mandated reconciliation attempts",
                    "📊 Evidence and witness hearings",
                    "⚖️  Final judgment and implementation"
                ]
        
        elif domain == 'commercial':
            steps = [
                "📧 Commercial dispute notice",
                "🤝 Arbitration/mediation attempt",
                "📝 Commercial court filing",
                "📊 Expert evidence and hearings",
                "⚖️  Commercial judgment and enforcement"
            ]
    def _generate_remedies(self, sections: List[Section], domain: str, jurisdiction: str) -> List[str]:
        """Generate comprehensive available remedies"""
        remedies = []
        
        # Check for specific offense types
        is_sexual_offence = any('375' in s.section_number or '376' in s.section_number or 
                               '63' in s.section_number or '64' in s.section_number or
                               'rape' in s.section_id.lower() for s in sections)
        
        is_serious_crime = any(word in s.text.lower() for s in sections 
                              for word in ['murder', 'homicide', 'terrorism', 'trafficking'])
        
        if is_sexual_offence:
            if jurisdiction == 'IN':
                remedies = [
                    "🔒 Criminal prosecution with rigorous imprisonment (minimum 7 years, may extend to life)",
                    "💰 Compensation under Section 357A CrPC (up to ₹10 lakhs)",
                    "⚖️  Free legal aid under Legal Services Authorities Act",
                    "🛡️  Protection under Witness Protection Scheme",
                    "🏥 Medical treatment at government expense",
                    "🏠 Shelter and rehabilitation services",
                    "📞 24/7 helpline support (1091 Women Helpline)"
                ]
            elif jurisdiction == 'UK':
                remedies = [
                    "🔒 Criminal prosecution with life imprisonment possible",
                    "💰 Criminal Injuries Compensation Authority (CICA) claim",
                    "⚖️  Special measures for vulnerable witnesses",
                    "🛡️  Restraining orders and protection",
                    "🏥 NHS counseling and medical support"
                ]
            elif jurisdiction == 'UAE':
                remedies = [
                    "🔒 Criminal prosecution with severe penalties",
                    "💰 Diya (blood money) compensation",
                    "⚖️  Court-ordered compensation",
                    "🛡️  Protection orders",
                    "🏥 Medical and psychological support"
                ]
        
        elif is_serious_crime:
            if jurisdiction == 'IN':
                remedies = [
                    "🔒 Criminal prosecution with life imprisonment/death penalty",
                    "💰 Victim compensation under CrPC",
                    "⚖️  Free legal aid",
                    "🛡️  Witness protection",
                    "📈 Appeal to higher courts"
                ]
            else:
                remedies = [
                    "🔒 Criminal prosecution with maximum penalties",
                    "💰 Victim compensation schemes",
                    "⚖️  Legal aid and support",
                    "🛡️  Protection measures"
                ]
        
        else:
            # Extract remedies from section metadata
            for section in sections:
                if hasattr(section, 'metadata') and section.metadata:
                    if 'civil_remedies' in section.metadata:
                        section_remedies = section.metadata['civil_remedies']
                        if isinstance(section_remedies, list):
                            remedies.extend([f"⚖️  {remedy}" for remedy in section_remedies])
                        else:
                            remedies.append(f"⚖️  {section_remedies}")
                    
                    if 'punishment' in section.metadata:
                        remedies.append(f"🔒 Criminal: {section.metadata['punishment']}")
            
            # Default remedies by domain if none found
            if not remedies:
                if domain == 'criminal':
                    if jurisdiction == 'IN':
                        remedies = [
                            "🔒 Criminal prosecution and imprisonment/fine as per law",
                            "💰 Compensation under Section 357A CrPC",
                            "⚖️  Legal aid if eligible"
                        ]
                    elif jurisdiction == 'UK':
                        remedies = [
                            "🔒 Criminal prosecution and sentencing",
                            "💰 Criminal Injuries Compensation",
                            "⚖️  Legal aid if eligible"
                        ]
                    elif jurisdiction == 'UAE':
                        remedies = [
                            "🔒 Criminal prosecution and penalties",
                            "💰 Court-ordered compensation",
                            "⚖️  Legal representation"
                        ]
                
                elif domain == 'civil':
                    remedies = [
                        "💰 Monetary damages and compensation",
                        "⚖️  Specific performance of contract",
                        "🚫 Injunctive relief",
                        "🔄 Restitution and restoration"
                    ]
                
                elif domain == 'family':
                    if jurisdiction == 'IN':
                        remedies = [
                            "👨👩👧👦 Child custody and visitation rights",
                            "💰 Maintenance and alimony",
                            "🏠 Property settlement",
                            "🛡️  Protection orders if needed"
                        ]
                    else:
                        remedies = [
                            "👨👩👧👦 Child arrangements orders",
                            "💰 Financial settlements",
                            "🏠 Property division",
                            "🛡️  Non-molestation orders"
                        ]
                
                elif domain == 'commercial':
                    remedies = [
                        "💰 Breach of contract damages",
                        "⚖️  Specific performance",
                        "🚫 Injunctive relief",
                        "🔄 Rescission and restitution",
                        "📊 Account of profits"
                    ]
        
        return remedies[:8]  # Limit to top 8 remedies
    
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
        trace_id = legal_query.trace_id or f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
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
            "domain": domain,
            "available_jurisdictions": list(self.jurisdiction_sections.keys()),
            "total_sections": len(self.sections)
        })
        
        # Search relevant sections using multi-strategy approach
        relevant_sections = self.multi_strategy_search(legal_query.query_text, jurisdiction, domain)
        
        # Generate analysis
        legal_analysis = self._generate_legal_analysis(legal_query.query_text, relevant_sections, jurisdiction)
        procedural_steps = self._generate_procedural_steps(relevant_sections, domain, jurisdiction)
        remedies = self._generate_remedies(relevant_sections, domain, jurisdiction)
        
        # Calculate enhanced confidence score
        confidence_score = 0.1  # Base confidence
        if relevant_sections:
            # Base score from number of sections
            confidence_score += min(0.6, len(relevant_sections) * 0.1)
            
            # Boost for exact matches
            query_lower = legal_query.query_text.lower()
            for section in relevant_sections:
                if any(word in section.text.lower() for word in query_lower.split() if len(word) > 3):
                    confidence_score += 0.05
            
            # Boost for jurisdiction-specific sections
            jurisdiction_sections_count = len([s for s in relevant_sections if s.jurisdiction.value == jurisdiction])
            confidence_score += min(0.2, jurisdiction_sections_count * 0.02)
            
            # Cap at 0.95
            confidence_score = min(0.95, confidence_score)
        
        # Log completion
        self._log_enforcement_event("advice_generated", trace_id, {
            "sections_found": len(relevant_sections),
            "confidence_score": confidence_score,
            "jurisdiction_final": jurisdiction,
            "domain_final": domain,
            "procedural_steps_count": len(procedural_steps),
            "remedies_count": len(remedies)
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
    
    def save_enforcement_ledger(self, filename: str = "enhanced_legal_advice_ledger.json"):
        """Save enforcement ledger to file"""
        with open(filename, 'w') as f:
            json.dump(self.enforcement_ledger, f, indent=2)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        jurisdiction_stats = {}
        for jurisdiction, sections in self.jurisdiction_sections.items():
            jurisdiction_stats[jurisdiction] = {
                "total_sections": len(sections),
                "acts": len(set(s.act_id for s in sections)),
                "sample_acts": list(set(s.act_id for s in sections))[:5]
            }
        
        return {
            "total_sections": len(self.sections),
            "total_acts": len(self.acts),
            "total_cases": len(self.cases),
            "jurisdictions": jurisdiction_stats,
            "index_size": len(self.section_index),
            "crime_mappings": {j: len(crimes) for j, crimes in self.crime_mappings.items()}
        }

def main():
    """Demo the enhanced integrated legal advisor"""
    print("🚀 Initializing Enhanced Nyaya AI Legal Advisor...")
    advisor = EnhancedLegalAdvisor()
    
    # Display system statistics
    stats = advisor.get_system_stats()
    print(f"\n📊 System Statistics:")
    print(f"   Total Legal Sections: {stats['total_sections']}")
    print(f"   Total Acts: {stats['total_acts']}")
    print(f"   Jurisdictions: {', '.join(stats['jurisdictions'].keys())}")
    print(f"   Search Index Size: {stats['index_size']} keywords")
    
    # Comprehensive test queries
    test_queries = [
        LegalQuery("What is the punishment for theft in India?", "India", "criminal"),
        LegalQuery("I was raped in Delhi. What legal action can I take?", "India", "criminal"),
        LegalQuery("How to file for divorce in UK?", "UK", "family"),
        LegalQuery("What are the requirements for LLC formation in UAE?", "UAE", "commercial"),
        LegalQuery("Can I get compensation for medical negligence in India?", "India", "civil"),
        LegalQuery("Someone is stalking me in Mumbai. What can I do?", "India", "criminal"),
        LegalQuery("My employer in Dubai is not paying salary. What are my rights?", "UAE", "civil"),
        LegalQuery("I want to start a company in London. What's the process?", "UK", "commercial"),
        LegalQuery("Dowry harassment case in India - what sections apply?", "India", "criminal"),
        LegalQuery("Cybercrime fraud in UAE - need legal help", "UAE", "criminal")
    ]
    
    print(f"\n{'='*80}")
    print("🏛️  ENHANCED NYAYA AI LEGAL ADVISOR - COMPREHENSIVE TESTING")
    print(f"{'='*80}\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"📋 Query {i}: {query.query_text}")
        print(f"{'─'*80}")
        
        try:
            advice = advisor.provide_legal_advice(query)
            
            print(f"🌍 Jurisdiction: {advice.jurisdiction}")
            print(f"⚖️  Domain: {advice.domain}")
            print(f"📊 Confidence: {advice.confidence_score:.2f}")
            print(f"📚 Relevant Sections Found: {len(advice.relevant_sections)}")
            
            if advice.relevant_sections:
                print(f"\n📖 Top Relevant Sections:")
                for j, section in enumerate(advice.relevant_sections[:3], 1):
                    print(f"   {j}. Section {section.section_number}: {section.text[:100]}...")
            
            print(f"\n📝 Legal Analysis Preview:")
            analysis_preview = advice.legal_analysis[:400] + "..." if len(advice.legal_analysis) > 400 else advice.legal_analysis
            print(f"   {analysis_preview}")
            
            print(f"\n🔄 Procedural Steps ({len(advice.procedural_steps)} total):")
            for step in advice.procedural_steps[:4]:
                print(f"   • {step}")
            if len(advice.procedural_steps) > 4:
                print(f"   ... and {len(advice.procedural_steps) - 4} more steps")
            
            print(f"\n⚖️  Available Remedies ({len(advice.remedies)} total):")
            for remedy in advice.remedies[:4]:
                print(f"   • {remedy}")
            if len(advice.remedies) > 4:
                print(f"   ... and {len(advice.remedies) - 4} more remedies")
            
            print(f"\n🔍 Trace ID: {advice.trace_id}")
            
        except Exception as e:
            print(f"❌ Error processing query: {str(e)}")
        
        print(f"\n{'='*80}\n")
    
    # Save enforcement ledger
    advisor.save_enforcement_ledger()
    print(f"💾 Enhanced enforcement ledger saved with {len(advisor.enforcement_ledger)} events")
    
    # Display final statistics
    print(f"\n📈 Final System Performance:")
    print(f"   Queries Processed: {len(test_queries)}")
    print(f"   Average Sections per Query: {sum(len(advisor.provide_legal_advice(q).relevant_sections) for q in test_queries[:3]) / 3:.1f}")
    print(f"   Jurisdictions Covered: {len(stats['jurisdictions'])}")
    print(f"   Total Legal Database Size: {stats['total_sections']} sections")

if __name__ == "__main__":
    main()