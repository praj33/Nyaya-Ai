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
from procedures.loader import procedure_loader

# Try to import semantic search (optional)
try:
    from semantic_search import SemanticLegalSearch
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

# Import BM25 search (always available)
from bm25_search import LegalBM25Search

# Statute constants for specific query types
LAND_DISPUTE_STATUTES = [
    {
        "act": "Transfer of Property Act, 1882",
        "year": 1882,
        "section": "54",
        "title": "Sale of immovable property"
    },
    {
        "act": "Registration Act, 1908",
        "year": 1908,
        "section": "17",
        "title": "Documents of which registration is compulsory"
    },
    {
        "act": "Specific Relief Act, 1963",
        "year": 1963,
        "section": "16",
        "title": "Personal bars to relief"
    },
    {
        "act": "Code of Civil Procedure, 1908",
        "year": 1908,
        "section": "9",
        "title": "Courts to try all civil suits unless barred"
    },
    {
        "act": "Limitation Act, 1963",
        "year": 1963,
        "section": "65",
        "title": "Suit for possession of immovable property"
    },
    {
        "act": "Indian Evidence Act, 1872",
        "year": 1872,
        "section": "91",
        "title": "Evidence of terms of contracts reduced to writing"
    }
]

# Act metadata mapping for proper statute formatting
ACT_METADATA = {
    # Indian Acts
    'bns_sections': {'name': 'Bharatiya Nyaya Sanhita', 'year': 2023},
    'ipc_sections': {'name': 'Indian Penal Code', 'year': 1860},
    'crpc_sections': {'name': 'Code of Criminal Procedure', 'year': 1973},
    'bnss_sections': {'name': 'Bharatiya Nagarik Suraksha Sanhita', 'year': 2023},
    'cpc_sections': {'name': 'Code of Civil Procedure', 'year': 1908},
    'indian_evidence_act': {'name': 'Indian Evidence Act', 'year': 1872},
    'it_act_2000': {'name': 'Information Technology Act', 'year': 2000},
    'hindu_marriage_act': {'name': 'Hindu Marriage Act', 'year': 1955},
    'special_marriage_act': {'name': 'Special Marriage Act', 'year': 1954},
    'domestic_violence_act': {'name': 'Protection of Women from Domestic Violence Act', 'year': 2005},
    'dowry_prohibition_act': {'name': 'Dowry Prohibition Act', 'year': 1961},
    'consumer_protection_act': {'name': 'Consumer Protection Act', 'year': 2019},
    'motor_vehicles_act': {'name': 'Motor Vehicles Act', 'year': 1988},
    'uapa_1967': {'name': 'Unlawful Activities (Prevention) Act', 'year': 1967},
    'labour_employment_laws': {'name': 'Labour and Employment Laws', 'year': 1948},
    'property_real_estate_laws': {'name': 'Real Estate (Regulation and Development) Act', 'year': 2016},
    'farmers_protection_act': {'name': 'Farmers Protection Act', 'year': 2020},
    
    # UK Acts
    'uk_theft_act': {'name': 'Theft Act', 'year': 1968},
    'uk_fraud_act': {'name': 'Fraud Act', 'year': 2006},
    'uk_offences_against_person': {'name': 'Offences Against the Person Act', 'year': 1861},
    'uk_sexual_offences': {'name': 'Sexual Offences Act', 'year': 2003},
    'uk_misuse_drugs': {'name': 'Misuse of Drugs Act', 'year': 1971},
    'uk_computer_misuse': {'name': 'Computer Misuse Act', 'year': 1990},
    'uk_criminal_law': {'name': 'UK Criminal Law', 'year': 2023},
    'uk_human_rights_act_1998': {'name': 'Human Rights Act', 'year': 1998},
    'uk_law_dataset': {'name': 'UK Criminal Code', 'year': 2023},
    'uk_equality_act_2010': {'name': 'Equality Act', 'year': 2010},
    'uk_road_traffic_act_1988': {'name': 'Road Traffic Act', 'year': 1988},
    
    # UAE Acts
    'uae_penal_code': {'name': 'UAE Penal Code', 'year': 1987},
    'uae_cybercrime_law': {'name': 'UAE Cybercrime Law', 'year': 2012},
    'uae_personal_status_law': {'name': 'UAE Personal Status Law', 'year': 2005},
    'uae_comprehensive_laws_reference': {'name': 'UAE Federal Laws', 'year': 2021},
    'uae_law_dataset': {'name': 'UAE Legal Code', 'year': 2021},
    'uae_personal_status_map': {'name': 'UAE Personal Status Law', 'year': 2005},
    'uae_traffic_law_federal_law_no_21_1995': {'name': 'UAE Traffic Law', 'year': 1995},
    'uae_anti_narcotics_law_federal_law_no_14_1995': {'name': 'UAE Anti-Narcotics Law', 'year': 1995},
}

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
        import os
        if os.path.exists("Nyaya_AI/db"):
            db_path = "Nyaya_AI/db"
        elif os.path.exists("db"):
            db_path = "db"
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "db")
            if not os.path.exists(db_path):
                db_path = os.path.join(os.path.dirname(current_dir), "db")
        
        self.loader = JSONLoader(db_path)
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
                'adultery': ['13'],  # Hindu Marriage Act Section 13 - Divorce on grounds of adultery
                'cheating': ['318', '319', '415', '416', '417', '418', '419', '420'],
                'medical_negligence': ['304A', '336', '337', '338'],  # Causing death/hurt by negligence
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
                'accident': ['279', '304A', '337', '338', '40', '41', '42', '43', '44'],  # IPC + MVA accident sections
                'bike_accident': ['279', '304A', '337', '338', '40', '41', '42', '43', '44'],
                'car_accident': ['279', '304A', '337', '338', '40', '41', '42', '43', '44'],
                'road_accident': ['279', '304A', '337', '338', '40', '41', '42', '43', '44'],
                'vehicle_accident': ['279', '304A', '337', '338', '40', '41', '42', '43', '44'],
                'drunk_driving': ['185', '279', '304A', '30', '31', '32', '33', '34'],  # IPC + MVA drunk driving
                'rash_driving': ['279', '304A', '337', '338', '43', '44'],
                'negligent_driving': ['279', '304A', '337', '338', '43', '44'],
                'traffic_violation': ['177', '178', '179', '183', '184', '185', '20', '21', '22', '23', '24', '25', '26'],
                'traffic': ['177', '178', '179', '183', '184', '185', '20', '21', '22', '23', '24', '25', '26'],
                'signal': ['177', '178', '179', '183', '184', '185', '21'],  # Red light jumping
                'speeding': ['177', '178', '179', '183', '184', '185', '20'],  # Over-speeding
                'challan': ['177', '178', '179', '183', '184', '185', '20', '21', '22', '23', '24', '25', '26'],
                'helmet': ['24'],  # Not wearing helmet
                'seatbelt': ['23'],  # Not wearing seatbelt
                'license': ['3', '4', '5', '6', '7'],  # Driving license related
                'insurance': ['10', '11', '12', '13', '14'],  # Vehicle insurance
                'hit_and_run': ['14', '42', '279', '304A'],  # Hit and run cases
                'juvenile_driving': ['70', '71', '72'],  # Underage driving
                'suicide': ['305', '306', '309'],  # Abetment of suicide, attempt to suicide (IPC)
                'abetment_suicide': ['305', '306'],  # Abetment of suicide
            },
            'UK': {
                'theft': ['section_1_theft'],
                'robbery': ['section_8_robbery'],
                'burglary': ['section_9_burglary'],
                'fraud': ['section_1_fraud_by_false_representation', 'section_2_fraud_by_failure_to_disclose', 'section_3_fraud_by_abuse_of_position'],
                'assault': ['section_18_wounding_with_intent', 'section_20_malicious_wounding', 'section_39_common_assault'],
                'rape': ['section_1_rape', 'section_2_assault_by_penetration', 'section_3_sexual_assault', 'section_4_causing_sexual_activity'],
                'sexual_assault': ['section_1_rape', 'section_2_assault_by_penetration', 'section_3_sexual_assault'],
                'sexual_harassment': ['section_3_sexual_assault'],
                'drugs': ['section_4_production_and_supply', 'section_5_possession'],
                'cybercrime': ['section_1_unauthorised_access', 'section_2_unauthorised_access_with_intent', 'section_3_unauthorised_modification'],
                'hacking': ['section_1_unauthorised_access', 'section_2_unauthorised_access_with_intent'],
                'accident': ['section_1_causing_death_by_dangerous_driving', 'section_2_dangerous_driving'],
                'dangerous_driving': ['section_1_causing_death_by_dangerous_driving', 'section_2_dangerous_driving'],
                'drunk_driving': ['section_4_driving_with_excess_alcohol', 'section_5_driving_under_influence'],
                'traffic_violation': ['section_4_driving_with_excess_alcohol', 'section_5_driving_under_influence'],
                'terrorism': ['section_1_terrorism_act', 'section_11_membership', 'section_15_fundraising', 'section_5_preparation'],
                'terrorist_attack': ['section_1_terrorism_act', 'section_5_preparation'],
                'suicide': ['section_2_suicide_act'],
            },
            'UAE': {
                'theft': ['theft_article_391', 'article_391', 'Article_391', '391'],
                'robbery': ['robbery_article_392', 'article_392', 'Article_392', '392'],
                'assault': ['assault_article_333', 'article_333', 'Article_333', '333'],
                'beating': ['assault_article_333', 'article_333', 'Article_333', '333'],
                'domestic_violence': ['assault_article_333', 'article_333', 'Article_333', '333'],
                'violence': ['assault_article_333', 'article_333', 'Article_333', '333'],
                'defamation': ['defamation_article_372', 'article_372', 'Article_372', '372'],
                'rape': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'sexual_assault': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'sexual_harassment': ['article_359', 'Article_359', '359'],
                'cybercrime': ['unauthorized_access_article_3', 'data_interference_article_4', 'cyber_fraud_article_6', 'article_3', 'article_4', 'article_6', 'Article_3', 'Article_4', 'Article_6'],
                'hacking': ['unauthorized_access_article_3', 'data_interference_article_4', 'article_3', 'article_4', 'Article_3', 'Article_4'],
                'drugs': ['possession_article_39', 'trafficking_article_40', 'article_39', 'article_40', 'Article_39', 'Article_40'],
                'accident': ['article_1', 'Article_1', 'drunk_driving_article_62'],
                'traffic_violation': ['article_1', 'Article_1', 'drunk_driving_article_62'],
                'drunk_driving': ['drunk_driving_article_62', 'article_62', 'Article_62', '62'],
                'terrorism': ['article_1', 'article_2', 'Article_1', 'Article_2', '1', '2'],
                'terrorist_attack': ['article_1', 'article_2', 'Article_1', 'Article_2', '1', '2'],
                'suicide': ['article_340', 'Article_340', '340'],
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
        
        # PRIORITY 1: Marital cruelty/domestic violence (ALWAYS criminal + family)
        marital_cruelty_keywords = ['dowry', '498a', 'dowry death', 'dowry harassment', 
                                    'husband harass', 'husband beat', 'husband torture', 
                                    'husband abuse', 'husband threat', 'cruelty', 'beating',
                                    'torture', 'forced money', 'burning', 'asking for money',
                                    'demanding money', 'money demand', 'cash demand', 'domestic violence']
        if any(keyword in query_lower for keyword in marital_cruelty_keywords):
            return ['criminal', 'family']
        
        # PRIORITY 2: Terrorism
        terrorism_keywords = ['terrorism', 'terrorist', 'extremism', 'unlawful activities']
        if any(keyword in query_lower for keyword in terrorism_keywords):
            return ['terrorism']
        
        # PRIORITY 3: Serious crimes (check before civil to avoid misclassification)
        serious_crime_keywords = ['theft', 'murder', 'assault', 'rape', 'robbery', 'fraud', 'kidnapping',
                                 'crime', 'criminal', 'police', 'fir', 'arrest', 'hack', 'cyber', 'phishing',
                                 'identity theft', 'data breach', 'unauthorized access', 'snatch', 'steal',
                                 'died', 'death', 'killed', 'harass', 'harassment', 'violence', 'attack',
                                 'suicide', 'abetment', 'attempt to suicide']
        if any(keyword in query_lower for keyword in serious_crime_keywords):
            return ['criminal']
        
        # PRIORITY 4: Traffic/Vehicle offenses (criminal)
        traffic_keywords = ['accident', 'drunk', 'rash driving', 'hit and run', 'car accident', 
                           'road accident', 'vehicle', 'bike', 'traffic', 'signal', 'speeding', 
                           'over speed', 'challan', 'driving', 'license', 'vehicle accident']
        if any(keyword in query_lower for keyword in traffic_keywords):
            return ['criminal']
        
        # PRIORITY 5: Property seizure (civil unless criminal context)
        property_seizure_indicators = ['home was seized', 'house was seized', 'property was seized',
                                       'home seized', 'house seized', 'property seized',
                                       'seized my home', 'seized my house', 'seized my property',
                                       'illegal seizure', 'wrongful seizure', 'attachment of property']
        if any(indicator in query_lower for indicator in property_seizure_indicators):
            criminal_context = ['criminal case', 'crime proceeds', 'illegal assets', 'money laundering', 'drug']
            if not any(ctx in query_lower for ctx in criminal_context):
                return ['civil']
            return ['criminal']
        
        # PRIORITY 6: Civil disputes (explicit civil indicators)
        civil_indicators = ['sue', 'recover money', 'remaining amount', 'payment dispute', 'breach of contract',
                           'refund', 'invoice', 'non-payment', 'agreement', 'damages', 'compensation',
                           'contract', 'civil suit', 'money recovery', 'debt recovery', 'negligence',
                           'medical negligence', 'doctor', 'hospital', 'treatment', 'malpractice']
        if any(indicator in query_lower for indicator in civil_indicators):
            return ['civil']
        
        # PRIORITY 7: Consumer issues
        consumer_indicators = ['defective product', 'warranty', 'overcharging', 'service deficiency',
                              'consumer complaint', 'consumer forum', 'product quality', 'seller refused']
        if any(indicator in query_lower for indicator in consumer_indicators):
            return ['consumer']
        
        # PRIORITY 8: Property/Land disputes (civil)
        property_keywords = ['property', 'tenant', 'landlord', 'eviction', 'rent', 'lease', 'mortgage',
                            'land', 'dispute', 'boundary', 'title deed', 'encroachment', 'easement', 
                            'ownership', 'possession', 'foreclosure', 'attachment']
        if any(keyword in query_lower for keyword in property_keywords):
            return ['civil']
        
        # PRIORITY 9: Family law
        family_keywords = ['divorce', 'marriage', 'custody', 'alimony', 'maintenance', 'matrimonial',
                          'spouse', 'wife', 'husband', 'separation', 'guardianship', 'adoption',
                          'cheating', 'adultery', 'affair', 'unfaithful']
        if any(keyword in query_lower for keyword in family_keywords):
            return ['family']
        
        # PRIORITY 10: Employment/Labour
        employment_keywords = ['salary', 'wages', 'termination', 'fired', 'workplace',
                              'employee', 'employer', 'leave', 'overtime', 'gratuity', 'provident fund']
        if any(keyword in query_lower for keyword in employment_keywords):
            return ['commercial']
        
        # PRIORITY 11: Commercial/Agricultural
        commercial_keywords = ['contract', 'company', 'business', 'trade', 'corporate', 'partnership',
                              'farmer', 'crop', 'agricultural', 'farm', 'harvest', 'cultivation',
                              'msp', 'insurance', 'loan', 'debt']
        if any(keyword in query_lower for keyword in commercial_keywords):
            return ['commercial']
        
        # PRIORITY 12: Consumer (general)
        consumer_general = ['consumer', 'defective', 'refund']
        if any(keyword in query_lower for keyword in consumer_general):
            return ['consumer']
        
        # DEFAULT: Civil (safest fallback)
        return ['civil']
    
    def _search_relevant_sections(self, query: str, jurisdiction: str, domain: str) -> List[Section]:
        """Enhanced section search with BM25 ranking and act filtering"""
        
        # Get allowed act_ids from ontology
        allowed_act_ids = self.ontology_filter.get_allowed_act_ids(domain)
        
        matched_sections = []
        query_lower = query.lower()
        
        # Strategy 1: PRIORITIZE crime mappings (highest priority)
        crime_mapping_triggered = False
        if jurisdiction in self.crime_mappings:
            for crime, section_numbers in self.crime_mappings[jurisdiction].items():
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
                
                # Fuzzy match
                if not match_found:
                    for query_word in query_lower.split():
                        if len(query_word) > 3:
                            for crime_word in crime_words:
                                if len(crime_word) > 3:
                                    if query_word[:4] == crime_word[:4]:
                                        match_found = True
                                        break
                        if match_found:
                            break
                
                if match_found:
                    crime_mapping_triggered = True
                    for section in self.sections:
                        if section.jurisdiction.value == jurisdiction:
                            # Flexible matching: check if section_number contains any of the mapped numbers
                            # or if any mapped number is in the section_number
                            section_matches = any(
                                mapped_num in section.section_number or section.section_number in mapped_num
                                for mapped_num in section_numbers
                            )
                            if section_matches:
                                # TEMPORARY: Skip BNS sections for accidents until database is fixed
                                if crime in ['accident', 'bike_accident', 'car_accident', 'road_accident', 'vehicle_accident', 
                                       'drunk_driving', 'rash_driving', 'negligent_driving'] and 'bns' in section.act_id.lower():
                                    continue
                                
                                # Give VERY HIGH priority to crime mapping matches
                                if crime in ['terrorism', 'terrorist_attack']:
                                    if section.section_number == '113' and 'bns' in section.act_id.lower():
                                        matched_sections.append((section, 200))  # Highest priority
                                    elif section.section_number == '66F' and 'it_act' in section.act_id.lower():
                                        matched_sections.append((section, 195))
                                    else:
                                        matched_sections.append((section, 180))
                                elif crime in ['rape', 'sexual_assault', 'sexual_harassment']:
                                    matched_sections.append((section, 190))  # Very high for sexual offences
                                elif crime in ['cybercrime', 'hacking', 'identity_theft', 'cyber_terrorism']:
                                    if 'it_act' in section.act_id.lower():
                                        matched_sections.append((section, 180))
                                    else:
                                        matched_sections.append((section, 100))
                                else:
                                    matched_sections.append((section, 150))  # High priority for all crime mappings
        
        # Strategy 2: Use BM25 only if crime mapping didn't trigger OR as supplementary
        bm25_results = self.bm25_search.search(query, jurisdiction, top_k=50)
        for section, score in bm25_results:
            # Exclude defense/procedural sections (but allow CPC for civil domain)
            exclude_titles = ['accident in doing', 'lawful act', 'repeal', 'savings']
            if domain != 'civil':
                exclude_titles.extend(['commencement', 'short title', 'definitions', 'extent', 'application'])
            
            if any(keyword in section.text.lower()[:80] for keyword in exclude_titles):
                continue
            
            # Lower priority for BM25 results
            matched_sections.append((section, score * 5 if not crime_mapping_triggered else score * 2))
        
        # Special handling for family law queries
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
            # Skip sections with very low scores
            if score < 2:
                continue
            
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
            # Property -> Property Laws (check BEFORE agriculture)
            {
                'keywords': ['property', 'tenant', 'landlord', 'eviction', 'rent', 'lease', 'mortgage', 'rera', 'builder', 'flat', 'house', 'apartment', 'real estate', 'ownership', 'land dispute', 'boundary dispute', 'title deed', 'encroachment'],
                'acts': ['property', 'real_estate'],
                'min_sections': 2
            },
            # Agriculture -> Farmers Protection Act
            {
                'keywords': ['farmer', 'crop', 'agricultural', 'farm', 'harvest', 'cultivation', 'msp', 'kisan', 'agriculture', 'farming', 'irrigation', 'seed', 'fertilizer'],
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
                'keywords': ['accident', 'vehicle', 'car', 'bike', 'motorcycle', 'scooter', 'driving', 'license', 'insurance', 'traffic', 'challan', 'fine', 'road', 'collision', 'hit', 'drunk', 'speed', 'died', 'death', 'killed', 'rash', 'negligent'],
                'acts': ['motor_vehicles', 'ipc', 'bns'],
                'min_sections': 2
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
        """Generate comprehensive procedural steps with outcomes, timelines, and risk information"""
        jurisdiction_map = {'IN': 'india', 'UK': 'uk', 'UAE': 'uae'}
        country = jurisdiction_map.get(jurisdiction, 'india').lower()
        
        # Map terrorism domain to criminal
        if domain == 'terrorism':
            domain = 'criminal'
        
        # Map consumer to consumer_commercial
        if domain == 'consumer':
            domain = 'consumer_commercial'
        
        procedure = procedure_loader.get_procedure(country, domain.lower())
        
        if procedure and "procedure" in procedure and "steps" in procedure["procedure"]:
            steps = procedure["procedure"]["steps"]
            detailed_steps = []
            
            for step in steps:
                # Base step with title and description
                step_text = f"{step.get('title', '')}: {step.get('description', '')}"
                
                # Add conditional branches if available
                if 'conditional_branches' in step and step['conditional_branches']:
                    branches = step['conditional_branches']
                    outcomes = []
                    for branch in branches:
                        condition = branch.get('condition', '')
                        effect = branch.get('effect', '')
                        if condition and effect:
                            outcomes.append(f"{condition} -> {effect}")
                    if outcomes:
                        step_text += f" | Possible outcomes: {'; '.join(outcomes)}"
                
                # Add outcome intelligence if available
                if 'outcome_intelligence' in step and step['outcome_intelligence']:
                    intel = step['outcome_intelligence']
                    if 'typical_outcomes' in intel and intel['typical_outcomes']:
                        typical = ', '.join(intel['typical_outcomes'][:2])  # Show top 2
                        step_text += f" | Typical outcomes: {typical}"
                
                # Add risk flags if high risk
                if 'risk_flags' in step and step['risk_flags']:
                    risks = step['risk_flags']
                    if risks.get('high_risk_case') or (risks.get('failure_risks') and len(risks['failure_risks']) > 0):
                        failure_risks = risks.get('failure_risks', [])
                        if failure_risks:
                            step_text += f" | Key risks: {failure_risks[0]}"
                
                detailed_steps.append(step_text)
            
            # Add timeline information at the end
            if 'timelines' in procedure['procedure']:
                timelines = procedure['procedure']['timelines']
                timeline_text = f"Expected Timeline: Best case: {timelines.get('best_case', 'N/A')}, Average: {timelines.get('average', 'N/A')}, Worst case: {timelines.get('worst_case', 'N/A')}"
                detailed_steps.append(timeline_text)
            
            return detailed_steps
        
        return ["Consult legal counsel", "Gather evidence", "File appropriate action"]
    
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
        
        # Apply ontology filter (skip for family domain and non-Indian jurisdictions)
        allowed_act_ids = self.ontology_filter.get_allowed_act_ids(domain)
        if domain == 'family' or jurisdiction != 'IN':
            # For family domain or non-Indian jurisdictions, don't filter - allow all found sections
            filtered_sections = relevant_sections
            ontology_filtered = False
        else:
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
        addon_subtype = self.addon_resolver.detect_addon_subtype(legal_query.query_text, jurisdiction)
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
                
                # Enhanced title for rape sections
                enhanced_title = completed.get('title', completed['act'])
                section_num = completed['section']
                
                if section_num in ['63', '64', '65', '66', '375', '376', '376A', '376AB', '376B', '376C', '376D']:
                    if section_num == '63':
                        enhanced_title = "Rape - Penetration without consent (BNS 2023)"
                    elif section_num == '64':
                        enhanced_title = "Punishment for rape - Rigorous imprisonment 10 years to life (BNS 2023)"
                    elif section_num == '65':
                        enhanced_title = "Punishment for rape in certain cases - Enhanced penalties for aggravated circumstances (BNS 2023)"
                    elif section_num == '66':
                        enhanced_title = "Punishment for causing death or persistent vegetative state of victim - Life imprisonment or death (BNS 2023)"
                    elif section_num == '375':
                        enhanced_title = "Rape - Sexual intercourse without consent or with minor (IPC 1860)"
                    elif section_num == '376':
                        enhanced_title = "Punishment for rape - Rigorous imprisonment minimum 7 years, may extend to life (IPC 1860)"
                    elif section_num == '376A':
                        enhanced_title = "Punishment for causing death or resulting in persistent vegetative state - Minimum 20 years to life or death (IPC 1860)"
                    elif section_num == '376AB':
                        enhanced_title = "Punishment for rape on woman under 12 years - Rigorous imprisonment minimum 20 years to life or death (IPC 1860)"
                    elif section_num == '376B':
                        enhanced_title = "Sexual intercourse by husband upon his wife during separation - Imprisonment up to 2 years (IPC 1860)"
                    elif section_num == '376C':
                        enhanced_title = "Sexual intercourse by person in authority - Rigorous imprisonment 5-10 years (IPC 1860)"
                    elif section_num == '376D':
                        enhanced_title = "Gang rape - Rigorous imprisonment minimum 20 years to life (IPC 1860)"
                
                addon_statutes.append({
                    'act': completed['act'],
                    'year': completed.get('year', 0),
                    'section': completed['section'],
                    'title': enhanced_title
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
        all_statutes = []
        for section in relevant_sections:
            act_id_lower = section.act_id.lower() if section.act_id else ''
            act_metadata = None
            
            # Find matching act metadata
            for act_key, metadata in ACT_METADATA.items():
                if act_key.lower() in act_id_lower or act_id_lower in act_key.lower():
                    act_metadata = metadata
                    break
            
            # Enhanced title for rape sections
            enhanced_title = section.text[:100] if len(section.text) > 100 else section.text
            
            # Add detailed description for rape sections
            if section.section_number in ['63', '64', '65', '66', '375', '376', '376A', '376AB', '376B', '376C', '376D']:
                if section.section_number == '63':
                    enhanced_title = "Rape - Penetration without consent (BNS 2023)"
                elif section.section_number == '64':
                    enhanced_title = "Punishment for rape - Rigorous imprisonment 10 years to life (BNS 2023)"
                elif section.section_number == '65':
                    enhanced_title = "Punishment for rape in certain cases - Enhanced penalties for aggravated circumstances (BNS 2023)"
                elif section.section_number == '66':
                    enhanced_title = "Punishment for causing death or persistent vegetative state of victim - Life imprisonment or death (BNS 2023)"
                elif section.section_number == '375':
                    enhanced_title = "Rape - Sexual intercourse without consent or with minor (IPC 1860)"
                elif section.section_number == '376':
                    enhanced_title = "Punishment for rape - Rigorous imprisonment minimum 7 years, may extend to life (IPC 1860)"
                elif section.section_number == '376A':
                    enhanced_title = "Punishment for causing death or resulting in persistent vegetative state - Minimum 20 years to life or death (IPC 1860)"
                elif section.section_number == '376AB':
                    enhanced_title = "Punishment for rape on woman under 12 years - Rigorous imprisonment minimum 20 years to life or death (IPC 1860)"
                elif section.section_number == '376B':
                    enhanced_title = "Sexual intercourse by husband upon his wife during separation - Imprisonment up to 2 years (IPC 1860)"
                elif section.section_number == '376C':
                    enhanced_title = "Sexual intercourse by person in authority - Rigorous imprisonment 5-10 years (IPC 1860)"
                elif section.section_number == '376D':
                    enhanced_title = "Gang rape - Rigorous imprisonment minimum 20 years to life (IPC 1860)"
            
            if act_metadata:
                all_statutes.append({
                    'act': act_metadata['name'],
                    'year': act_metadata['year'],
                    'section': section.section_number,
                    'title': enhanced_title
                })
            else:
                all_statutes.append({
                    'act': section.act_id.replace('_', ' ').title() if section.act_id else 'Unknown Act',
                    'year': 0,
                    'section': section.section_number,
                    'title': enhanced_title
                })
        
        all_statutes.extend(addon_statutes)
        
        all_statutes, dowry_filtered = self.dowry_precision.filter_and_prioritize(all_statutes, legal_query.query_text)
        
        # Boost confidence for dowry cases
        if dowry_filtered:
            confidence_score = self.dowry_precision.boost_confidence(all_statutes)
            ontology_filtered = True
        
        # Check for land dispute queries and use predefined statutes (India only)
        query_lower = legal_query.query_text.lower()
        if jurisdiction == 'IN' and any(keyword in query_lower for keyword in ['land dispute', 'property dispute', 'land', 'boundary', 'title deed', 'encroachment']):
            all_statutes = LAND_DISPUTE_STATUTES.copy()
        
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