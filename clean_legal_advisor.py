import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

# Import existing components
import sys
import os
sys.path.append('.')

from data_bridge.loader import JSONLoader
from data_bridge.schemas.section import Section, Jurisdiction
from events.event_types import EventType
from core.ontology.ontology_filter import OntologyFilter
from core.addons.addon_subtype_resolver import AddonSubtypeResolver
from core.addons.dowry_precision_layer import DowryPrecisionLayer

# Try to import semantic search (optional)
try:
    from semantic_search import SemanticLegalSearch
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

# Import BM25 search (always available)
from bm25_search import LegalBM25Search

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
    statutes: List[Dict[str, Any]] = field(default_factory=list)
    case_laws: List[Dict[str, Any]] = field(default_factory=list)
    constitutional_articles: List[str] = field(default_factory=list)
    timeline: List[Dict[str, str]] = field(default_factory=list)
    glossary: List[Dict[str, str]] = field(default_factory=list)
    evidence_requirements: List[str] = field(default_factory=list)
    enforcement_decision: str = "ALLOW"
    ontology_filtered: bool = False

class EnhancedLegalAdvisor:
    def __init__(self):
        self.loader = JSONLoader("db")
        self.sections, self.acts, self.cases = self.loader.load_and_normalize_directory()
        self.enforcement_ledger = []
        self.ontology_filter = OntologyFilter()
        self.addon_resolver = AddonSubtypeResolver()
        self.dowry_precision = DowryPrecisionLayer()
        
        # Create comprehensive searchable indexes
        self.section_index = self._build_section_index()
        self.jurisdiction_sections = self._build_jurisdiction_index()
        self.crime_mappings = self._build_crime_mappings()
        
        # Initialize semantic search if available
        self.semantic_search = None
        if SEMANTIC_SEARCH_AVAILABLE:
            try:
                self.semantic_search = SemanticLegalSearch()
            except Exception as e:
                print(f"WARNING: Semantic search initialization failed: {e}")
        
        # Initialize BM25 search (always available)
        self.bm25_search = LegalBM25Search()
        self.bm25_search.index_sections(self.sections)
        
        print(f"Enhanced Legal Advisor loaded:")
        print(f"  - {len(self.sections)} sections")
        print(f"  - {len(self.acts)} acts") 
        print(f"  - {len(self.cases)} cases")
        print(f"  - {len(self.jurisdiction_sections)} jurisdictions")
        print(f"  - BM25 full-text search: ENABLED")
        if self.semantic_search:
            print(f"  - AI semantic search: ENABLED")
        
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
                'robbery': ['309', '310', '311', '312', '390', '391', '392', '393', '394', '395', '396', '397', '398'],
                'snatching': ['309', '356', '390', '392'],
                'chain_snatching': ['309', '356', '390', '392'],
                'extortion': ['308', '383', '384', '385', '386', '387', '388', '389'],
                'stalking': ['78', '354D'],
                'sexual_harassment': ['75', '354A'],
                'dowry_death': ['80', '304B'],
                'domestic_violence': ['85', '498A'],
                'cybercrime': ['43', '43A', '66', '66B', '66C', '66D', '66E', '66F', '67', '67A', '67B'],
                'hacking': ['66', '66B', '66C', '70'],
                'identity_theft': ['66C'],
                'cyber_terrorism': ['66F'],
                'farmer_loss': ['10', '11', '26', '27', '28'],
                'crop_damage': ['10', '11', '26', '27'],
                'agricultural_debt': ['7', '8', '9'],
                'farmer_compensation': ['10', '11', '12', '26', '27', '28'],
                'consumer_complaint': ['10', '20', '40', '50'],
                'defective_product': ['20', '21', '40', '41', '42'],
                'workplace_harassment': ['30', '31', '34'],
                'wrongful_termination': ['20', '23'],
                'salary_dispute': ['1', '2', '3'],
                'terrorism': ['113', '66F'],
                'terrorist_attack': ['113', '66F'],
                'property_dispute': ['40', '41', '42', '43'],
                'tenant_eviction': ['20', '22', '23'],
                'accident': ['40', '43', '44', '50'],
                'drunk_driving': ['30', '31'],
                'traffic_violation': ['20', '21', '22', '23', '24']
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
                'hacking': ['section_1_unauthorised_access', 'section_2_unauthorised_access_with_intent']
            },
            'UAE': {
                'theft': ['article_391'],
                'robbery': ['article_392'],
                'assault': ['article_333'],
                'defamation': ['article_372'],
                'cybercrime': ['unauthorized_access_article_3', 'data_interference_article_4', 'cyber_fraud_article_6'],
                'hacking': ['unauthorized_access_article_3', 'data_interference_article_4'],
                'drugs': ['possession_article_39', 'trafficking_article_40']
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
        """Enhanced domain detection - returns primary domain"""
        domains = self._detect_domains(query, hint)
        return domains[0] if domains else 'civil'
    
    def _detect_domains(self, query: str, hint: Optional[str] = None) -> List[str]:
        """Enhanced domain detection - returns list of applicable domains"""
        query_lower = query.lower()
        
        # Domain Re-evaluation Layer - semantic sanity check overrides hint
        civil_indicators = ['sue', 'recover money', 'remaining amount', 'payment dispute', 'breach of contract',
                           'refund', 'invoice', 'non-payment', 'agreement', 'damages', 'compensation',
                           'contract', 'civil suit', 'money recovery', 'debt recovery']
        
        consumer_indicators = ['defective product', 'warranty', 'overcharging', 'service deficiency',
                              'consumer complaint', 'consumer forum', 'product quality', 'seller refused']
        
        # Check civil indicators first
        if any(indicator in query_lower for indicator in civil_indicators):
            return ['civil']
        
        # Check consumer indicators
        if any(indicator in query_lower for indicator in consumer_indicators):
            return ['consumer']
        
        # Marital cruelty is ALWAYS criminal + family
        marital_cruelty_keywords = ['dowry', '498a', 'dowry death', 'dowry harassment', 
                                    'husband harass', 'husband beat', 'husband torture', 
                                    'husband abuse', 'husband threat', 'cruelty', 'beating',
                                    'torture', 'forced money', 'burning', 'asking for money',
                                    'demanding money', 'money demand', 'cash demand']
        if any(keyword in query_lower for keyword in marital_cruelty_keywords):
            return ['criminal', 'family']
        
        # Terrorism
        terrorism_keywords = ['terrorism', 'terrorist', 'extremism', 'unlawful activities']
        if any(keyword in query_lower for keyword in terrorism_keywords):
            return ['terrorism']
        
        # Criminal law keywords
        criminal_keywords = ['theft', 'murder', 'assault', 'rape', 'robbery', 'fraud', 'kidnapping',
                           'crime', 'criminal', 'police', 'fir', 'arrest', 'hack', 'cyber', 'phishing',
                           'identity theft', 'data breach', 'unauthorized access', 'snatch', 'steal',
                           'accident', 'drunk', 'rash driving', 'hit and run', 'harass', 'harassment']
        
        # Family law keywords
        family_keywords = ['divorce', 'marriage', 'custody', 'alimony', 'maintenance', 'matrimonial',
                          'spouse', 'wife', 'husband', 'separation', 'guardianship', 'adoption']
        
        # Civil law keywords
        civil_keywords = ['property', 'tenant', 'landlord', 'eviction', 'rent', 'lease', 'mortgage',
                         'consumer', 'defective', 'refund', 'compensation', 'negligence']
        
        # Employment/Labour keywords
        employment_keywords = ['salary', 'wages', 'termination', 'fired', 'workplace',
                              'employee', 'employer', 'leave', 'overtime', 'gratuity', 'provident fund']
        
        # Commercial/Agricultural keywords
        commercial_keywords = ['contract', 'company', 'business', 'trade', 'corporate', 'partnership',
                              'farmer', 'crop', 'agricultural', 'farm', 'harvest', 'cultivation',
                              'msp', 'insurance', 'loan', 'debt']
        
        # Check for criminal keywords
        if any(keyword in query_lower for keyword in criminal_keywords):
            return ['criminal']
        
        # Check for family keywords
        if any(keyword in query_lower for keyword in family_keywords):
            return ['family']
        
        # Check for employment keywords
        if any(keyword in query_lower for keyword in employment_keywords):
            return ['commercial']
        
        # Check for civil keywords
        if any(keyword in query_lower for keyword in civil_keywords):
            return ['civil']
        
        # Check for commercial/agricultural keywords
        if any(keyword in query_lower for keyword in commercial_keywords):
            return ['commercial']
        
        # Use hint only if no strong semantic indicators found
        if hint:
            return [hint.lower()]
        
        return ['civil']
    
    def _search_relevant_sections(self, query: str, jurisdiction: str, domain: str) -> List[Section]:
        """Enhanced section search with BM25 ranking and act filtering"""
        
        # Get allowed act_ids from ontology
        allowed_act_ids = self.ontology_filter.get_allowed_act_ids(domain)
        
        # Strategy 1: Use BM25 for initial ranking
        bm25_results = self.bm25_search.search(query, jurisdiction, top_k=50)
        matched_sections = [(section, score * 10) for section, score in bm25_results]  # Scale BM25 scores
        
        # Strategy 2: Boost with crime mappings
        query_lower = query.lower()
        if jurisdiction in self.crime_mappings:
            for crime, section_numbers in self.crime_mappings[jurisdiction].items():
                # Check for exact match or partial match (e.g., "hacked" matches "hacking")
                crime_words = crime.split('_')
                match_found = False
                
                # Exact crime match
                if crime in query_lower:
                    match_found = True
                
                # Check if any crime word is in query
                if not match_found:
                    for crime_word in crime_words:
                        if crime_word in query_lower:
                            match_found = True
                            break
                
                # Fuzzy match: check if query words share common root with crime words
                # e.g., "hacked" shares "hack" with "hacking"
                if not match_found:
                    for query_word in query_lower.split():
                        if len(query_word) > 3:
                            for crime_word in crime_words:
                                if len(crime_word) > 3:
                                    # Check if first 4 characters match (hack == hack)
                                    if query_word[:4] == crime_word[:4]:
                                        match_found = True
                                        break
                        if match_found:
                            break
                
                if match_found:
                    for section in self.sections:
                        if (section.jurisdiction.value == jurisdiction and 
                            section.section_number in section_numbers):
                            # For terrorism, prioritize BNS 113 and IT Act 66F
                            if crime in ['terrorism', 'terrorist_attack']:
                                if section.section_number == '113' and 'bns' in section.act_id.lower():
                                    matched_sections.append((section, 25))  # Highest priority for BNS 113
                                elif section.section_number == '66F' and 'it_act' in section.act_id.lower():
                                    matched_sections.append((section, 24))  # High priority for IT Act 66F
                            # For cybercrime, prioritize IT Act sections
                            elif crime in ['cybercrime', 'hacking', 'identity_theft', 'cyber_terrorism']:
                                if 'it_act' in section.act_id.lower():
                                    matched_sections.append((section, 20))  # Highest priority for IT Act
                                else:
                                    matched_sections.append((section, 5))  # Lower priority for other acts
                            else:
                                matched_sections.append((section, 15))  # Normal priority
        
        # Strategy 1.5: Act-specific search for family law
        if domain == 'family' and jurisdiction == 'IN':
            # Search Hindu Marriage Act sections
            for section in self.sections:
                if (section.jurisdiction.value == jurisdiction and 
                    'hindu_marriage_act' in section.act_id.lower()):
                    matched_sections.append((section, 12))  # High priority for family domain
        
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
        
        # Sort by relevance
        sorted_sections = sorted(unique_sections.values(), key=lambda x: x[1], reverse=True)
        
        # Smart act-based filtering - Route queries to specific acts based on keywords
        query_lower = query.lower()
        
        # Define act routing rules with semantic categories
        act_filters = [
            # Cybercrime -> IT Act
            {
                'keywords': ['hack', 'cyber', 'phishing', 'data breach', 'computer', 'online fraud', 'digital', 'internet', 'email', 'website', 'password', 'account', 'unauthorized access'],
                'acts': ['it_act'],
                'min_sections': 4
            },
            # Agriculture -> Farmers Protection Act
            {
                'keywords': ['farmer', 'crop', 'agricultural', 'farm', 'harvest', 'cultivation', 'msp', 'kisan', 'agriculture', 'farming', 'land', 'irrigation', 'seed', 'fertilizer'],
                'acts': ['farmers_protection'],
                'min_sections': 3
            },
            # Employment -> Labour Laws
            {
                'keywords': ['salary', 'wages', 'fired', 'termination', 'boss', 'employer', 'employee', 'workplace', 'leave', 'overtime', 'gratuity', 'pf', 'epf', 'job', 'work', 'office', 'company', 'resignation', 'dismissal', 'harassment'],
                'acts': ['labour', 'employment'],
                'min_sections': 3
            },
            # Consumer -> Consumer Protection Act
            {
                'keywords': ['defective', 'product', 'refund', 'consumer', 'warranty', 'guarantee', 'shop', 'purchase', 'bought', 'seller', 'buyer', 'goods', 'service', 'complaint', 'quality'],
                'acts': ['consumer_protection'],
                'min_sections': 3
            },
            # Property -> Property Laws
            {
                'keywords': ['property', 'tenant', 'landlord', 'eviction', 'rent', 'lease', 'mortgage', 'rera', 'builder', 'flat', 'house', 'apartment', 'real estate', 'land', 'ownership'],
                'acts': ['property', 'real_estate'],
                'min_sections': 3
            },
            # Traffic -> Motor Vehicles Act
            {
                'keywords': ['accident', 'vehicle', 'car', 'bike', 'driving', 'license', 'insurance', 'traffic', 'challan', 'fine', 'road', 'collision', 'hit', 'drunk', 'speed'],
                'acts': ['motor_vehicles'],
                'min_sections': 3
            },
            # Family -> Marriage Acts
            {
                'keywords': ['divorce', 'marriage', 'custody', 'alimony', 'maintenance', 'spouse', 'wife', 'husband', 'child', 'separation', 'matrimonial', 'family'],
                'acts': ['hindu_marriage', 'special_marriage', 'domestic_violence'],
                'min_sections': 3
            }
        ]
        
        # Multi-keyword matching with scoring
        best_match = None
        best_score = 0
        
        # Try semantic search first if available
        if self.semantic_search:
            act_descriptions = {
                'it_act': 'cybercrime hacking computer internet digital fraud phishing data breach online security',
                'farmers_protection': 'farmer agriculture crop cultivation farming land irrigation seed fertilizer harvest',
                'labour': 'employment salary wages job work termination firing workplace employee employer',
                'consumer_protection': 'consumer product defective refund warranty purchase goods service quality',
                'property': 'property real estate tenant landlord rent lease mortgage house flat building',
                'motor_vehicles': 'vehicle car accident driving license insurance traffic road collision',
                'hindu_marriage': 'marriage divorce custody alimony spouse wife husband family matrimonial'
            }
            
            best_act = self.semantic_search.find_best_act(query, act_descriptions)
            if best_act:
                # Find matching filter rule
                for filter_rule in act_filters:
                    if any(best_act in act for act in filter_rule['acts']):
                        best_match = filter_rule
                        best_score = 10  # High score for semantic match
                        break
        
        # Fallback to keyword matching if semantic search not available or no match
        if not best_match:
            for filter_rule in act_filters:
                # Count how many keywords match
                match_count = sum(1 for keyword in filter_rule['keywords'] if keyword in query_lower)
                
                if match_count > best_score:
                    best_score = match_count
                    best_match = filter_rule
        
        # If we have a strong match (2+ keywords or semantic match), filter by that act
        if best_match and best_score >= 2:
            filtered_sections = [
                (s, score) for s, score in sorted_sections 
                if any(act in s.act_id.lower() for act in best_match['acts'])
            ]
            
            # If we have enough sections from specific acts, use only those
            if len(filtered_sections) >= best_match['min_sections']:
                return [section for section, score in filtered_sections[:10]]
        
        # Otherwise return top 10
        return [section for section, score in sorted_sections[:10]]
    
    def _apply_ontology_filter(self, sections: List[Section], allowed_act_ids: Set[str]) -> List[Section]:
        """Filter sections by allowed act_ids"""
        if not allowed_act_ids:
            return []
        
        filtered = []
        for section in sections:
            normalized_act_id = self.ontology_filter.normalize_act_id(section.act_id)
            if normalized_act_id in allowed_act_ids:
                filtered.append(section)
        
        return filtered
    
    def _generate_legal_analysis(self, query: str, sections: List[Section], jurisdiction: str) -> str:
        """Generate comprehensive legal analysis based on relevant sections"""
        if not sections:
            return f"No specific legal provisions found for this query in {jurisdiction} jurisdiction. Please provide more specific details or consult a legal professional."
        
        query_lower = query.lower()
        analysis = f"Legal Analysis for {jurisdiction} Jurisdiction:\n\n"
        
        # Add context-specific analysis
        if any(word in query_lower for word in ['rape', 'sexual assault', 'sexual harassment']):
            analysis += "*** SERIOUS CRIMINAL MATTER - SEXUAL OFFENCE ***\n"
            analysis += "This involves grave criminal charges with severe penalties. Immediate legal action required.\n\n"
        elif any(word in query_lower for word in ['murder', 'homicide', 'killing']):
            analysis += "*** SERIOUS CRIMINAL MATTER - HOMICIDE ***\n"
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
                    analysis += f"   Punishment: {section.metadata['punishment']}\n"
                if 'civil_remedies' in section.metadata:
                    remedies = section.metadata['civil_remedies']
                    if isinstance(remedies, list):
                        analysis += f"   Remedies: {', '.join(remedies)}\n"
                    else:
                        analysis += f"   Remedies: {remedies}\n"
                if 'elements_required' in section.metadata:
                    elements = section.metadata['elements_required']
                    if isinstance(elements, list):
                        analysis += f"   Required Elements: {', '.join(elements)}\n"
            
            analysis += "\n"
        
        # Add jurisdiction-specific notes
        if jurisdiction == 'IN':
            analysis += "Indian Legal System Notes:\n"
            analysis += "- Cases are tried under Indian Penal Code (IPC) or Bharatiya Nyaya Sanhita (BNS)\n"
            analysis += "- Criminal cases: Police investigation -> Charge sheet -> Trial -> Judgment\n"
            analysis += "- Civil cases: Plaint filing -> Written statement -> Evidence -> Judgment\n"
        elif jurisdiction == 'UK':
            analysis += "UK Legal System Notes:\n"
            analysis += "- Criminal cases: Police investigation -> CPS charging -> Court trial\n"
            analysis += "- Civil cases: County Court or High Court depending on value\n"
            analysis += "- Legal aid may be available for qualifying cases\n"
        elif jurisdiction == 'UAE':
            analysis += "UAE Legal System Notes:\n"
            analysis += "- Federal and local laws apply depending on emirate\n"
            analysis += "- Sharia principles influence family and personal status matters\n"
            analysis += "- Mediation often mandatory before court proceedings\n"
        
        return analysis
    
    def _generate_procedural_steps(self, sections: List[Section], domain: str, jurisdiction: str, query: str = "", domains: List[str] = None) -> List[str]:
        """Generate detailed procedural steps based on sections, domain, and jurisdiction"""
        steps = []
        query_lower = query.lower()
        
        if domains is None:
            domains = [domain]
        
        # Check for marital cruelty (hybrid criminal-family)
        is_marital_cruelty = 'criminal' in domains and 'family' in domains
        
        if is_marital_cruelty:
            if jurisdiction == 'IN':
                steps = [
                    "IMMEDIATE: File FIR at nearest police station under IPC 498A/BNS 85 (Cruelty) and Dowry Prohibition Act",
                    "Medical examination if physical injuries present (within 24 hours)",
                    "Apply for protection order under Domestic Violence Act Section 18",
                    "Apply for residence order to secure matrimonial home (DV Act Section 19)",
                    "Police investigation and evidence collection",
                    "Charge sheet filing by prosecution",
                    "Criminal trial in Sessions Court",
                    "Parallel: File petition for divorce on grounds of cruelty (Hindu Marriage Act Section 13)",
                    "Parallel: Claim maintenance and alimony (HMA Sections 25, 27)",
                    "Judgment and sentencing in criminal case",
                    "Divorce decree and financial settlement in family court"
                ]
            return steps
        
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
                        "IMMEDIATE: Report to police (FIR under Section 154 CrPC)",
                        "Medical examination and evidence collection (within 24 hours)",
                        "Police investigation under Section 173 CrPC",
                        "Charge sheet filing by prosecution",
                        "Fast-track court proceedings (mandatory under law)",
                        "In-camera trial to protect victim identity",
                        "Judgment and sentencing",
                        "Victim support services and compensation under Section 357A CrPC"
                    ]
                elif is_serious_crime:
                    steps = [
                        "Immediate police reporting and FIR registration",
                        "Detailed investigation and evidence collection",
                        "Senior police officer supervision",
                        "Charge sheet filing within 90 days",
                        "Sessions Court trial",
                        "Judgment and sentencing",
                        "Appeal options to High Court/Supreme Court"
                    ]
                else:
                    steps = [
                        "File FIR/Police complaint at nearest police station",
                        "Police investigation and evidence collection",
                        "Charge sheet filing by prosecution",
                        "Court proceedings and trial",
                        "Judgment and sentencing"
                    ]
            
            elif jurisdiction == 'UK':
                steps = [
                    "Report to police (999 for emergencies, 101 for non-emergencies)",
                    "Police investigation and evidence gathering",
                    "Crown Prosecution Service (CPS) charging decision",
                    "Magistrates' Court or Crown Court trial",
                    "Sentencing if convicted",
                    "Appeal options to Court of Appeal"
                ]
            
            elif jurisdiction == 'UAE':
                steps = [
                    "Report to police (999 emergency or local police station)",
                    "Police investigation and evidence collection",
                    "Public prosecution review and charging",
                    "Criminal court trial",
                    "Judgment and sentencing",
                    "Appeal to Court of Appeal and Cassation Court"
                ]
        
        elif domain == 'civil':
            if jurisdiction == 'IN':
                steps = [
                    "Send legal notice to opposing party (mandatory)",
                    "File civil recovery suit in appropriate court with jurisdiction",
                    "Serve summons and pleadings to defendant",
                    "Written statement filing by defendant",
                    "Evidence presentation and arguments",
                    "Final arguments",
                    "Court judgment and decree",
                    "Decree execution if required"
                ]
            
            elif jurisdiction == 'UK':
                steps = [
                    "Pre-action correspondence and protocol compliance",
                    "File claim in County Court or High Court",
                    "Serve claim on defendant",
                    "Defence filing and case management",
                    "Evidence exchange and trial",
                    "Judgment and enforcement"
                ]
            
            elif jurisdiction == 'UAE':
                steps = [
                    "Mandatory mediation attempt (in some emirates)",
                    "File civil claim in competent court",
                    "Serve claim documents on defendant",
                    "Defence filing and case preparation",
                    "Court hearings and evidence presentation",
                    "Judgment and execution"
                ]
        
        elif domain == 'consumer':
            if jurisdiction == 'IN':
                steps = [
                    "File consumer complaint with District Consumer Commission",
                    "Attach supporting documents (invoice, warranty, correspondence)",
                    "District Commission hearing",
                    "Order for refund/replacement/compensation",
                    "Appeal to State Commission (if required)",
                    "Appeal to National Commission (if required)"
                ]
            else:
                steps = [
                    "File consumer complaint",
                    "Hearing and evidence",
                    "Order",
                    "Appeal (if required)"
                ]
        
        elif domain == 'family':
            if jurisdiction == 'IN':
                # Check if it's a divorce query
                if any(word in query_lower for word in ['divorce', 'separation', 'dissolve marriage']):
                    steps = [
                        "Attempt mediation/counseling (recommended but not mandatory)",
                        "File divorce petition in family court under Hindu Marriage Act Section 13",
                        "Serve petition to spouse through court",
                        "Mandatory mediation session (Family Courts Act)",
                        "If mediation fails, proceed to evidence stage",
                        "Both parties present evidence and witnesses",
                        "Court may grant decree nisi (conditional divorce)",
                        "After 6 months, decree absolute (final divorce) granted",
                        "Settlement of maintenance, alimony, and custody matters"
                    ]
                else:
                    steps = [
                        "Attempt mediation/counseling (recommended)",
                        "File petition in family court",
                        "Mandatory mediation session",
                        "Evidence and witness examination",
                        "Final decree and implementation"
                    ]
            
            elif jurisdiction == 'UK':
                steps = [
                    "Mediation Information and Assessment Meeting (MIAM)",
                    "Family Court proceedings",
                    "CAFCASS involvement for children matters",
                    "First Hearing Dispute Resolution (FHDRA)",
                    "Final hearing with judgment"
                ]
            
            elif jurisdiction == 'UAE':
                steps = [
                    "Reconciliation committee involvement",
                    "Personal Status Court proceedings",
                    "Court-mandated reconciliation attempts",
                    "Evidence and witness hearings",
                    "Final judgment and implementation"
                ]
        
        elif domain == 'commercial':
            steps = [
                "Commercial dispute notice",
                "Arbitration/mediation attempt",
                "Commercial court filing",
                "Expert evidence and hearings",
                "Commercial judgment and enforcement"
            ]
        
        return steps
    
    def _generate_remedies(self, sections: List[Section], domain: str, jurisdiction: str, query: str = "") -> List[str]:
        """Generate comprehensive available remedies"""
        remedies = []
        query_lower = query.lower()
        
        # Check for specific offense types
        is_sexual_offence = any('375' in s.section_number or '376' in s.section_number or 
                               '63' in s.section_number or '64' in s.section_number or
                               'rape' in s.section_id.lower() for s in sections)
        
        is_serious_crime = any(word in s.text.lower() for s in sections 
                              for word in ['murder', 'homicide', 'terrorism', 'trafficking'])
        
        if is_sexual_offence:
            if jurisdiction == 'IN':
                remedies = [
                    "Criminal prosecution with rigorous imprisonment (minimum 7 years, may extend to life)",
                    "Compensation under Section 357A CrPC (up to Rs.10 lakhs)",
                    "Free legal aid under Legal Services Authorities Act",
                    "Protection under Witness Protection Scheme",
                    "Medical treatment at government expense",
                    "Shelter and rehabilitation services",
                    "24/7 helpline support (1091 Women Helpline)"
                ]
            elif jurisdiction == 'UK':
                remedies = [
                    "Criminal prosecution with life imprisonment possible",
                    "Criminal Injuries Compensation Authority (CICA) claim",
                    "Special measures for vulnerable witnesses",
                    "Restraining orders and protection",
                    "NHS counseling and medical support"
                ]
            elif jurisdiction == 'UAE':
                remedies = [
                    "Criminal prosecution with severe penalties",
                    "Diya (blood money) compensation",
                    "Court-ordered compensation",
                    "Protection orders",
                    "Medical and psychological support"
                ]
        
        elif is_serious_crime:
            if jurisdiction == 'IN':
                remedies = [
                    "Criminal prosecution with life imprisonment/death penalty",
                    "Victim compensation under CrPC",
                    "Free legal aid",
                    "Witness protection",
                    "Appeal to higher courts"
                ]
            else:
                remedies = [
                    "Criminal prosecution with maximum penalties",
                    "Victim compensation schemes",
                    "Legal aid and support",
                    "Protection measures"
                ]
        
        else:
            # Extract remedies from section metadata
            for section in sections:
                if hasattr(section, 'metadata') and section.metadata:
                    if 'civil_remedies' in section.metadata:
                        section_remedies = section.metadata['civil_remedies']
                        if isinstance(section_remedies, list):
                            remedies.extend([f"Legal: {remedy}" for remedy in section_remedies])
                        else:
                            remedies.append(f"Legal: {section_remedies}")
                    
                    if 'punishment' in section.metadata:
                        remedies.append(f"Criminal: {section.metadata['punishment']}")
            
            # Default remedies by domain if none found
            if not remedies:
                if domain == 'criminal':
                    if jurisdiction == 'IN':
                        remedies = [
                            "Criminal prosecution and imprisonment/fine as per law",
                            "Compensation under Section 357A CrPC",
                            "Legal aid if eligible"
                        ]
                    elif jurisdiction == 'UK':
                        remedies = [
                            "Criminal prosecution and sentencing",
                            "Criminal Injuries Compensation",
                            "Legal aid if eligible"
                        ]
                    elif jurisdiction == 'UAE':
                        remedies = [
                            "Criminal prosecution and penalties",
                            "Court-ordered compensation",
                            "Legal representation"
                        ]
                
                elif domain == 'civil':
                    remedies = [
                        "Monetary damages and compensation",
                        "Specific performance of contract",
                        "Injunctive relief",
                        "Restitution and restoration"
                    ]
                
                elif domain == 'family':
                    if jurisdiction == 'IN':
                        # Check if it's a divorce query
                        if any(word in query_lower for word in ['divorce', 'separation']):
                            remedies = [
                                "Divorce decree under Hindu Marriage Act Section 13",
                                "Child custody and visitation rights under Section 26",
                                "Maintenance and alimony under Sections 25 & 27",
                                "Property settlement and division",
                                "Protection orders if domestic violence involved",
                                "One-time permanent alimony or monthly maintenance"
                            ]
                        else:
                            remedies = [
                                "Child custody and visitation rights",
                                "Maintenance and alimony",
                                "Property settlement",
                                "Protection orders if needed"
                            ]
                    else:
                        remedies = [
                            "Child arrangements orders",
                            "Financial settlements",
                            "Property division",
                            "Non-molestation orders"
                        ]
                
                elif domain == 'commercial':
                    remedies = [
                        "Breach of contract damages",
                        "Specific performance",
                        "Injunctive relief",
                        "Rescission and restitution",
                        "Account of profits"
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
        
        # Detect jurisdiction and domains
        jurisdiction = self._detect_jurisdiction(legal_query.query_text, legal_query.jurisdiction_hint)
        domains = self._detect_domains(legal_query.query_text, legal_query.domain_hint)
        domain = domains[0] if domains else 'civil'
        
        # Log classification
        self._log_enforcement_event("jurisdiction_resolved", trace_id, {
            "jurisdiction": jurisdiction,
            "domain": domain,
            "domains": domains,
            "available_jurisdictions": list(self.jurisdiction_sections.keys()),
            "total_sections": len(self.sections)
        })
        
        # Search relevant sections
        relevant_sections = self._search_relevant_sections(legal_query.query_text, jurisdiction, domain)
        
        # Apply ontology filter
        allowed_act_ids = self.ontology_filter.get_allowed_act_ids(domain)
        filtered_sections = self._apply_ontology_filter(relevant_sections, allowed_act_ids)
        ontology_filtered = len(relevant_sections) != len(filtered_sections)
        
        # Limit to top 5 most relevant sections to avoid noise
        relevant_sections = filtered_sections[:5]
        
        # Generate analysis
        legal_analysis = self._generate_legal_analysis(legal_query.query_text, relevant_sections, jurisdiction)
        procedural_steps = self._generate_procedural_steps(relevant_sections, domain, jurisdiction, legal_query.query_text, domains)
        remedies = self._generate_remedies(relevant_sections, domain, jurisdiction, legal_query.query_text)
        
        # Calculate enhanced confidence score
        confidence_score = 0.1
        if relevant_sections:
            confidence_score += min(0.6, len(relevant_sections) * 0.1)
            
            query_lower = legal_query.query_text.lower()
            for section in relevant_sections:
                if any(word in section.text.lower() for word in query_lower.split() if len(word) > 3):
                    confidence_score += 0.05
            
            jurisdiction_sections_count = len([s for s in relevant_sections if s.jurisdiction.value == jurisdiction])
            confidence_score += min(0.2, jurisdiction_sections_count * 0.02)
            
            confidence_score = min(0.95, confidence_score)
        
        # Log completion
        self._log_enforcement_event("advice_generated", trace_id, {
            "sections_found": len(relevant_sections),
            "confidence_score": confidence_score,
            "jurisdiction_final": jurisdiction,
            "domain_final": domain,
            "domains_final": domains,
            "procedural_steps_count": len(procedural_steps),
            "remedies_count": len(remedies)
        })
        
        # Check addon subtypes for specialized offenses (prioritize over base retrieval)
        addon_subtype = self.addon_resolver.detect_addon_subtype(legal_query.query_text)
        addon_statutes = []
        constitutional_articles = []
        dowry_filtered = False
        
        if addon_subtype:
            addon_data = self.addon_resolver.addon_subtypes[addon_subtype]
            raw_statutes = addon_data.get('statutes', [])
            constitutional_articles = addon_data.get('constitutional_articles', [])
            
            # Apply statute overlay to complete years
            for s in raw_statutes:
                completed = self.addon_resolver._complete_statute_metadata(s)
                addon_statutes.append({
                    'act': completed['act'],
                    'year': completed.get('year', 0),
                    'section': completed['section'],
                    'title': completed.get('title', completed['act'])
                })
            
            # Apply offense subtype prioritization
            if addon_subtype == 'rape':
                include_keywords = ['rape', 'sexual assault', 'penetration', 'consent']
                exclude_keywords = ['importation', 'procuration', 'trafficking']
                addon_statutes = [
                    s for s in addon_statutes
                    if any(kw in s['title'].lower() for kw in include_keywords)
                    and not any(kw in s['title'].lower() for kw in exclude_keywords)
                ]
            
            # If addon provides statutes, use them as primary source
            if addon_statutes:
                relevant_sections = []  # Clear base retrieval
                ontology_filtered = False
        
        # Apply Dowry Precision Layer
        all_statutes = [{
            'act': section.act_id.replace('_', ' ').title() if section.act_id else 'Unknown Act',
            'year': 0,
            'section': section.section_number,
            'title': section.text[:100] if len(section.text) > 100 else section.text
        } for section in relevant_sections] + addon_statutes
        
        all_statutes, dowry_filtered = self.dowry_precision.filter_and_prioritize(all_statutes, legal_query.query_text)
        
        # Boost confidence for dowry cases
        if dowry_filtered:
            confidence_score = self.dowry_precision.boost_confidence(all_statutes)
            ontology_filtered = True
        
        # Store domains in advice object
        advice = LegalAdvice(
            query=legal_query.query_text,
            jurisdiction=jurisdiction,
            domain=domain,
            relevant_sections=relevant_sections,
            legal_analysis=legal_analysis,
            procedural_steps=procedural_steps,
            remedies=remedies,
            confidence_score=confidence_score,
            trace_id=trace_id,
            timestamp=datetime.now().isoformat(),
            statutes=all_statutes,
            case_laws=[],
            constitutional_articles=constitutional_articles,
            timeline=[],
            glossary=[],
            evidence_requirements=[],
            enforcement_decision="ALLOW",
            ontology_filtered=ontology_filtered or dowry_filtered
        )
        
        # Add domains as attribute
        advice.domains = domains
        
        return advice
    
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
    print(">> Initializing Enhanced Nyaya AI Legal Advisor...")
    advisor = EnhancedLegalAdvisor()
    
    # Display system statistics
    stats = advisor.get_system_stats()
    print(f"\n>> System Statistics:")
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
        LegalQuery("Dowry harassment case in India - what sections apply?", "India", "criminal"),
        LegalQuery("Cybercrime fraud in UAE - need legal help", "UAE", "criminal")
    ]
    
    print(f"\n{'='*80}")
    print(">> ENHANCED NYAYA AI LEGAL ADVISOR - COMPREHENSIVE TESTING")
    print(f"{'='*80}\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query.query_text}")
        print("-" * 80)
        
        try:
            advice = advisor.provide_legal_advice(query)
            
            print(f"Jurisdiction: {advice.jurisdiction}")
            print(f"Domain: {advice.domain}")
            print(f"Confidence: {advice.confidence_score:.2f}")
            print(f"Relevant Sections Found: {len(advice.relevant_sections)}")
            
            if advice.relevant_sections:
                print(f"\nTop Relevant Sections:")
                for j, section in enumerate(advice.relevant_sections[:3], 1):
                    print(f"   {j}. Section {section.section_number}: {section.text[:100]}...")
            
            print(f"\nLegal Analysis Preview:")
            analysis_preview = advice.legal_analysis[:400] + "..." if len(advice.legal_analysis) > 400 else advice.legal_analysis
            print(f"   {analysis_preview}")
            
            print(f"\nProcedural Steps ({len(advice.procedural_steps)} total):")
            for step in advice.procedural_steps[:4]:
                print(f"   • {step}")
            if len(advice.procedural_steps) > 4:
                print(f"   ... and {len(advice.procedural_steps) - 4} more steps")
            
            print(f"\nAvailable Remedies ({len(advice.remedies)} total):")
            for remedy in advice.remedies[:4]:
                print(f"   • {remedy}")
            if len(advice.remedies) > 4:
                print(f"   ... and {len(advice.remedies) - 4} more remedies")
            
            print(f"\nTrace ID: {advice.trace_id}")
            
        except Exception as e:
            print(f"ERROR processing query: {str(e)}")
        
        print(f"\n{'='*80}\n")
    
    # Save enforcement ledger
    advisor.save_enforcement_ledger()
    print(f">> Enhanced enforcement ledger saved with {len(advisor.enforcement_ledger)} events")
    
    # Display final statistics
    print(f"\n>> Final System Performance:")
    print(f"   Queries Processed: {len(test_queries)}")
    print(f"   Jurisdictions Covered: {len(stats['jurisdictions'])}")
    print(f"   Total Legal Database Size: {stats['total_sections']} sections")

if __name__ == "__main__":
    main()