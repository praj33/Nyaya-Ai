import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import re

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
from core.llm import groq_retrieval_augmentor
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

# Targeted statute overrides for common FAQ-style queries (India)
QUERY_STATUTE_OVERRIDES = [
    {
        "any": ["theft", "steal", "stolen"],
        "statutes": [
            {"act": "Indian Penal Code", "year": 1860, "section": "378", "title": "Theft"},
            {"act": "Indian Penal Code", "year": 1860, "section": "379", "title": "Punishment for theft"},
        ],
    },
    {
        "any": ["assault", "hit", "fight", "beating", "slapped", "hurt"],
        "statutes": [
            {"act": "Indian Penal Code", "year": 1860, "section": "319", "title": "Hurt"},
            {"act": "Indian Penal Code", "year": 1860, "section": "323", "title": "Punishment for voluntarily causing hurt"},
            {"act": "Indian Penal Code", "year": 1860, "section": "351", "title": "Assault"},
            {"act": "Indian Penal Code", "year": 1860, "section": "352", "title": "Punishment for assault or criminal force"},
        ],
    },
    {
        "any": ["cheating"],
        "exclude": ["husband", "wife", "spouse", "marriage", "adultery", "affair"],
        "statutes": [
            {"act": "Indian Penal Code", "year": 1860, "section": "415", "title": "Cheating"},
            {"act": "Indian Penal Code", "year": 1860, "section": "420", "title": "Cheating and dishonestly inducing delivery of property"},
        ],
    },
    {
        "any": ["verbal abuse", "abusive language", "insult"],
        "statutes": [
            {"act": "Indian Penal Code", "year": 1860, "section": "504", "title": "Intentional insult with intent to provoke breach of peace"},
            {"act": "Indian Penal Code", "year": 1860, "section": "509", "title": "Word, gesture or act intended to insult modesty of a woman"},
        ],
    },
    {
        "any": ["false complaint", "false police complaint", "false fir", "fake fir", "false case", "fake case"],
        "statutes": [
            {"act": "Indian Penal Code", "year": 1860, "section": "182", "title": "False information to public servant"},
            {"act": "Indian Penal Code", "year": 1860, "section": "211", "title": "False charge of offence with intent to injure"},
        ],
    },
    {
        "any": ["arrest without warrant"],
        "statutes": [
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "41", "title": "When police may arrest without warrant"},
        ],
    },
    {
        "any": ["domestic violence"],
        "statutes": [
            {"act": "Protection of Women from Domestic Violence Act", "year": 2005, "section": "3", "title": "Definition of domestic violence"},
            {"act": "Protection of Women from Domestic Violence Act", "year": 2005, "section": "12", "title": "Application to Magistrate"},
            {"act": "Protection of Women from Domestic Violence Act", "year": 2005, "section": "18", "title": "Protection orders"},
            {"act": "Indian Penal Code", "year": 1860, "section": "498A", "title": "Cruelty by husband or relatives"},
        ],
    },
    {
        "any": ["refuse to register fir", "police refuse to register fir", "refuse fir"],
        "statutes": [
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "154", "title": "Information in cognizable cases (FIR)"},
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "156", "title": "Police officer's power to investigate cognizable case"},
        ],
    },
    {
        "any": ["after fir", "after an fir", "after filing fir", "after an fir is filed"],
        "statutes": [
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "157", "title": "Procedure for investigation"},
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "173", "title": "Report of police officer on completion of investigation"},
        ],
    },
    {
        "any": ["fir"],
        "exclude": ["after fir", "refuse to register fir", "refuse fir", "after an fir", "after filing fir"],
        "statutes": [
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "154", "title": "Information in cognizable cases (FIR)"},
        ],
    },
    {
        "any": ["custody", "police custody"],
        "statutes": [
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "57", "title": "Person arrested not to be detained more than 24 hours"},
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "167", "title": "Procedure when investigation cannot be completed in 24 hours"},
        ],
    },
    {
        "any": ["difference between bail", "bail and anticipatory bail", "difference between bail and anticipatory bail"],
        "statutes": [
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "436", "title": "In what cases bail to be taken"},
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "437", "title": "Bail in non-bailable offences"},
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "439", "title": "Special powers of High Court or Court of Session regarding bail"},
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "438", "title": "Anticipatory bail"},
        ],
    },
    {
        "any": ["anticipatory bail"],
        "statutes": [
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "438", "title": "Direction for grant of bail to person apprehending arrest"},
        ],
    },
    {
        "any": ["bail"],
        "statutes": [
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "436", "title": "In what cases bail to be taken"},
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "437", "title": "Bail in non-bailable offences"},
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "439", "title": "Special powers of High Court or Court of Session regarding bail"},
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "438", "title": "Anticipatory bail"},
        ],
    },
    {
        "any": ["divorce"],
        "statutes": [
            {"act": "Hindu Marriage Act", "year": 1955, "section": "13", "title": "Divorce"},
            {"act": "Hindu Marriage Act", "year": 1955, "section": "13B", "title": "Divorce by mutual consent"},
        ],
    },
    {
        "any": ["maintenance after divorce", "maintenance"],
        "statutes": [
            {"act": "Hindu Marriage Act", "year": 1955, "section": "25", "title": "Permanent alimony and maintenance"},
            {"act": "Code of Criminal Procedure", "year": 1973, "section": "125", "title": "Order for maintenance of wives, children and parents"},
        ],
    },
    {
        "any": ["child custody"],
        "statutes": [
            {"act": "Hindu Marriage Act", "year": 1955, "section": "26", "title": "Custody of children"},
        ],
    },
    {
        "any": ["illegally occupies", "illegal occupation", "encroachment"],
        "statutes": [
            {"act": "Indian Penal Code", "year": 1860, "section": "441", "title": "Criminal trespass"},
            {"act": "Indian Penal Code", "year": 1860, "section": "447", "title": "Punishment for criminal trespass"},
        ],
    },
    {
        "any": ["adverse possession"],
        "statutes": [
            {"act": "Limitation Act", "year": 1963, "section": "65", "title": "Suit for possession of immovable property"},
        ],
    },
    {
        "any": ["sold without", "without the owner's consent", "without owner consent"],
        "statutes": [
            {"act": "Transfer of Property Act", "year": 1882, "section": "7", "title": "Persons competent to transfer"},
            {"act": "Transfer of Property Act", "year": 1882, "section": "54", "title": "Sale of immovable property"},
        ],
    },
    {
        "any": ["fraudulent property", "fraudulent sale", "forged signature", "fake signature", "forgery"],
        "statutes": [
            {"act": "Indian Penal Code", "year": 1860, "section": "420", "title": "Cheating and dishonestly inducing delivery of property"},
            {"act": "Indian Penal Code", "year": 1860, "section": "467", "title": "Forgery of valuable security, will, etc."},
            {"act": "Indian Penal Code", "year": 1860, "section": "468", "title": "Forgery for purpose of cheating"},
            {"act": "Indian Penal Code", "year": 1860, "section": "471", "title": "Using as genuine a forged document"},
        ],
    },
    {
        "any": ["home loan", "emi", "bank auction", "sarfaesi", "npa"],
        "statutes": [
            {"act": "SARFAESI Act", "year": 2002, "section": "13(2)", "title": "Demand notice for secured debt"},
            {"act": "SARFAESI Act", "year": 2002, "section": "13(4)", "title": "Measures for recovery by secured creditor"},
            {"act": "SARFAESI Act", "year": 2002, "section": "17", "title": "Appeal to DRT"},
        ],
    },
    {
        "any": ["defective product", "consumer court", "consumer complaint", "consumer forum", "consumer"],
        "statutes": [
            {"act": "Consumer Protection Act", "year": 2019, "section": "2", "title": "Consumer rights"},
            {"act": "Consumer Protection Act", "year": 2019, "section": "6", "title": "Right to seek redressal"},
            {"act": "Consumer Protection Act", "year": 2019, "section": "10", "title": "Unfair trade practices"},
        ],
    },
    {
        "any": ["loud music", "noise", "nuisance"],
        "statutes": [
            {"act": "Indian Penal Code", "year": 1860, "section": "268", "title": "Public nuisance"},
            {"act": "Indian Penal Code", "year": 1860, "section": "290", "title": "Punishment for public nuisance"},
        ],
    },
    {
        "any": ["fake information online", "posted fake information", "online defamation", "defamation online"],
        "statutes": [
            {"act": "Indian Penal Code", "year": 1860, "section": "499", "title": "Defamation"},
            {"act": "Indian Penal Code", "year": 1860, "section": "500", "title": "Punishment for defamation"},
            {"act": "Information Technology Act", "year": 2000, "section": "66C", "title": "Identity theft"},
            {"act": "Information Technology Act", "year": 2000, "section": "66D", "title": "Cheating by personation using computer resource"},
        ],
    },
    {
        "any": ["salary not paid", "unpaid salary", "salary for", "salary for 3 months", "not pay salary", "not paid salary"],
        "statutes": [
            {"act": "Labour and Employment Laws", "year": 1948, "section": "1", "title": "Payment of wages"},
            {"act": "Labour and Employment Laws", "year": 1948, "section": "2", "title": "Minimum wages"},
            {"act": "Labour and Employment Laws", "year": 1948, "section": "3", "title": "Timely payment of wages"},
        ],
    },
    {
        "any": ["security deposit", "deposit not returned"],
        "statutes": [
            {"act": "Indian Contract Act", "year": 1872, "section": "73", "title": "Compensation for loss or damage caused by breach of contract"},
            {"act": "Indian Contract Act", "year": 1872, "section": "74", "title": "Compensation for breach where penalty stipulated"},
        ],
    },
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
    'income_tax_act_1961': {'name': 'Income-tax Act', 'year': 1961},
    'cgst_act_2017': {'name': 'Central Goods and Services Tax Act', 'year': 2017},
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
    query_understanding: Dict[str, Any] = field(default_factory=dict)
    retrieval_metadata: Dict[str, Any] = field(default_factory=dict)

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
        self.groq_retrieval_augmentor = groq_retrieval_augmentor
        
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
                'breach_of_contract': ['73', '74'],  # Contract Act sections
                'contract_dispute': ['73', '74'],
                'partnership_dispute': ['1', '2', '3'],  # Partnership Act
                'company_dispute': ['1', '2', '3'],  # Companies Act
                'intellectual_property': ['1', '2', '3'],  # IP laws
                'trademark': ['1', '2', '3'],
                'copyright': ['1', '2', '3'],
                'patent': ['1', '2', '3'],
            },
            'UK': {
                'theft': ['section_1_theft'],
                'robbery': ['section_8_robbery'],
                'murder': ['murder', 'homicide', 'killing'],  # Will trigger addon
                'burglary': ['section_9_burglary'],
                'fraud': ['section_1_fraud_by_false_representation', 'section_2_fraud_by_failure_to_disclose', 'section_3_fraud_by_abuse_of_position'],
                'extortion': ['section_21_blackmail'],
                'blackmail': ['section_21_blackmail'],
                'demanding': ['section_21_blackmail'],
                'demanding_money': ['section_21_blackmail'],
                'demanding_dowry': ['section_21_blackmail'],
                'dowry': ['section_21_blackmail'],
                'assault': ['section_18_wounding_with_intent', 'section_20_malicious_wounding', 'section_39_common_assault'],
                'beating': ['section_18_wounding_with_intent', 'section_20_malicious_wounding', 'section_39_common_assault', 'section_47_actual_bodily_harm'],
                'domestic_violence': ['section_18_wounding_with_intent', 'section_20_malicious_wounding', 'section_39_common_assault', 'section_47_actual_bodily_harm'],
                'violence': ['section_18_wounding_with_intent', 'section_20_malicious_wounding', 'section_39_common_assault'],
                'rape': ['section_1_rape', 'section_2_assault_by_penetration', 'section_3_sexual_assault', 'section_4_causing_sexual_activity'],
                'raped': ['section_1_rape', 'section_2_assault_by_penetration', 'section_3_sexual_assault'],
                'raping': ['section_1_rape', 'section_2_assault_by_penetration', 'section_3_sexual_assault'],
                'sexual_assault': ['section_1_rape', 'section_2_assault_by_penetration', 'section_3_sexual_assault'],
                'sexual_harassment': ['section_3_sexual_assault'],
                'pedophile': ['section_1_rape', 'section_5_rape_of_child_under_13', 'section_9_sexual_activity_with_child'],
                'paedophile': ['section_1_rape', 'section_5_rape_of_child_under_13', 'section_9_sexual_activity_with_child'],
                'child_abuse': ['section_5_rape_of_child_under_13', 'section_9_sexual_activity_with_child'],
                'raping_child': ['section_5_rape_of_child_under_13', 'section_9_sexual_activity_with_child'],
                'raping_minor': ['section_5_rape_of_child_under_13', 'section_9_sexual_activity_with_child'],
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
                'breach_of_contract': ['section_1_contract_law'],
                'contract_dispute': ['section_1_contract_law'],
                'partnership_dispute': ['section_1_partnership_act'],
                'company_dispute': ['section_1_companies_act'],
                'intellectual_property': ['section_1_ip_law'],
                'trademark': ['section_1_trademarks_act'],
                'copyright': ['section_1_copyright_act'],
                'patent': ['section_1_patents_act'],
            },
            'UAE': {
                'theft': ['theft_article_391', 'article_391', 'Article_391', '391'],
                'robbery': ['robbery_article_392', 'article_392', 'Article_392', '392'],
                'murder': ['murder', 'homicide', 'killing'],  # Will trigger addon
                'assault': ['assault_article_333', 'article_333', 'Article_333', '333'],
                'beating': ['assault_article_333', 'article_333', 'Article_333', '333'],
                'domestic_violence': ['assault_article_333', 'article_333', 'Article_333', '333'],
                'violence': ['assault_article_333', 'article_333', 'Article_333', '333'],
                'extortion': ['article_399', 'Article_399', '399'],
                'demanding': ['article_399', 'Article_399', '399'],
                'demanding_money': ['article_399', 'Article_399', '399'],
                'demanding_dowry': ['article_399', 'Article_399', '399'],
                'dowry': ['article_399', 'Article_399', '399'],
                'defamation': ['defamation_article_372', 'article_372', 'Article_372', '372'],
                'rape': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'raped': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'raping': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'sexual_assault': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'sexual_harassment': ['article_359', 'Article_359', '359'],
                'pedophile': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'paedophile': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'child_abuse': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'raping_child': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'raping_minor': ['article_354', 'article_355', 'article_356', 'Article_354', 'Article_355', 'Article_356', '354', '355', '356'],
                'cybercrime': ['unauthorized_access_article_3', 'data_interference_article_4', 'cyber_fraud_article_6', 'article_3', 'article_4', 'article_6', 'Article_3', 'Article_4', 'Article_6'],
                'hacking': ['unauthorized_access_article_3', 'data_interference_article_4', 'article_3', 'article_4', 'Article_3', 'Article_4'],
                'drugs': ['possession_article_39', 'trafficking_article_40', 'article_39', 'article_40', 'Article_39', 'Article_40'],
                'accident': ['article_1', 'Article_1', 'drunk_driving_article_62'],
                'traffic_violation': ['article_1', 'Article_1', 'drunk_driving_article_62'],
                'drunk_driving': ['drunk_driving_article_62', 'article_62', 'Article_62', '62'],
                'terrorism': ['article_1', 'article_2', 'Article_1', 'Article_2', '1', '2'],
                'terrorist_attack': ['article_1', 'article_2', 'Article_1', 'Article_2', '1', '2'],
                'suicide': ['article_340', 'Article_340', '340'],
                'breach_of_contract': ['article_1', 'Article_1', '1'],
                'contract_dispute': ['article_1', 'Article_1', '1'],
                'partnership_dispute': ['article_1', 'Article_1', '1'],
                'company_dispute': ['article_1', 'Article_1', '1'],
                'intellectual_property': ['article_1', 'Article_1', '1'],
                'trademark': ['article_1', 'Article_1', '1'],
                'copyright': ['article_1', 'Article_1', '1'],
                'patent': ['article_1', 'Article_1', '1'],
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

        # PRIORITY 2.5: Property fraud disputes (civil)
        property_fraud_keywords = ['fraud', 'fraudulent', 'forged', 'forgery', 'fake signature', 'signature forged', 'scam']
        property_context = ['property', 'land', 'plot', 'house', 'flat', 'apartment', 'sale deed', 'registry', 'mutation', 'title deed']
        if any(keyword in query_lower for keyword in property_context) and any(keyword in query_lower for keyword in property_fraud_keywords):
            return ['civil']

        # PRIORITY 2.6: Marital cheating/adultery (family)
        if 'cheating' in query_lower and any(term in query_lower for term in ['husband', 'wife', 'spouse', 'marriage', 'adultery', 'affair']):
            return ['family']
        
        # PRIORITY 3: Serious crimes (check before civil to avoid misclassification)
        serious_crime_keywords = ['theft', 'murder', 'assault', 'rape', 'raped', 'raping', 'robbery', 'fraud', 'kidnapping',
                                 'crime', 'criminal', 'police', 'fir', 'arrest', 'hack', 'cyber', 'phishing',
                                 'identity theft', 'data breach', 'unauthorized access', 'snatch', 'steal',
                                 'died', 'death', 'killed', 'harass', 'harassment', 'violence', 'attack',
                                 'suicide', 'abetment', 'attempt to suicide', 'pedophile', 'paedophile',
                                 'child abuse', 'minor sexual', 'molested child', 'sex with child',
                                 'hit', 'fight', 'beating', 'slapped', 'hurt', 'cheating']
        if any(keyword in query_lower for keyword in serious_crime_keywords):
            return ['criminal']
        
        # PRIORITY 4: Traffic/Vehicle offenses (criminal)
        traffic_keywords = ['accident', 'drunk', 'rash driving', 'hit and run', 'car accident', 
                           'road accident', 'vehicle', 'bike', 'traffic', 'signal', 'speeding', 
                           'over speed', 'challan', 'driving', 'license', 'vehicle accident']
        if any(keyword in query_lower for keyword in traffic_keywords):
            return ['criminal']

        # PRIORITY 4.5: Police/procedure terms (criminal)
        procedure_keywords = ['bail', 'anticipatory bail', 'custody', 'remand', 'fir', 'f.i.r', 'police complaint', 'arrest without warrant']
        if any(keyword in query_lower for keyword in procedure_keywords):
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
        tax_indicators = ['income tax', 'tax evasion', 'tax avoidance', 'gst', 'cgst', 'igst', 'sgst',
                          'tds', 'input tax credit', 'itc', 'assessment order', 'fake invoice',
                          'bogus invoice', 'refund fraud', 'under-reported income', 'misreported income']
        if any(indicator in query_lower for indicator in tax_indicators):
            return ['civil']

        builder_delay_indicators = ['builder', 'building', 'not built', 'not build', 'project delay',
                                    'delay in possession', 'possession delay', 'delayed possession',
                                    'rera', 'construction delay', 'handover delay', 'flat handover']
        if any(indicator in query_lower for indicator in builder_delay_indicators):
            return ['civil']

        unpaid_wage_indicators = ['salary not paid', 'unpaid salary', 'wages not paid', 'unpaid wages',
                                  'boss is not paying me', 'boss not paying', 'employer not paying',
                                  'not paying me', 'pending salary', 'withheld wages']
        if any(indicator in query_lower for indicator in unpaid_wage_indicators):
            return ['civil']

        # PRIORITY 7: Consumer issues
        consumer_indicators = ['consumer', 'consumer court', 'consumer complaint', 'consumer forum',
                              'defective product', 'warranty', 'overcharging', 'service deficiency',
                              'product quality', 'seller refused']
        if any(indicator in query_lower for indicator in consumer_indicators):
            return ['consumer']

        # PRIORITY 8: Civil disputes (explicit civil indicators)
        civil_indicators = ['sue', 'recover money', 'remaining amount', 'payment dispute', 'breach of contract',
                           'refund', 'invoice', 'non-payment', 'agreement', 'damages', 'compensation',
                           'contract', 'civil suit', 'money recovery', 'debt recovery', 'negligence',
                           'medical negligence', 'doctor', 'hospital', 'treatment', 'malpractice',
                           'loan', 'emi', 'home loan', 'bank auction', 'borrower']
        if any(indicator in query_lower for indicator in civil_indicators):
            return ['civil']
        
        # PRIORITY 9: Property/Land disputes (civil)
        property_keywords = ['property', 'tenant', 'landlord', 'eviction', 'rent', 'lease', 'mortgage',
                            'land', 'dispute', 'boundary', 'title deed', 'encroachment', 'easement',
                            'ownership', 'possession', 'foreclosure', 'attachment', 'builder', 'building',
                            'rera', 'project', 'construction']
        if any(keyword in query_lower for keyword in property_keywords):
            return ['civil']
        
        # PRIORITY 10: Family law
        family_keywords = ['divorce', 'marriage', 'custody', 'alimony', 'maintenance', 'matrimonial',
                          'spouse', 'wife', 'husband', 'separation', 'guardianship', 'adoption',
                          'adultery', 'affair', 'unfaithful']
        if any(keyword in query_lower for keyword in family_keywords):
            return ['family']
        
        # PRIORITY 11: Employment/Labour
        employment_keywords = ['salary', 'wages', 'termination', 'fired', 'workplace',
                              'employee', 'employer', 'leave', 'overtime', 'gratuity', 'provident fund',
                              'boss', 'unpaid', 'pending salary', 'payment of wages', 'not paying']
        if any(keyword in query_lower for keyword in employment_keywords):
            return ['civil']
        
        # PRIORITY 12: Commercial/Agricultural
        commercial_keywords = ['contract', 'company', 'business', 'trade', 'corporate', 'partnership',
                              'farmer', 'crop', 'agricultural', 'farm', 'harvest', 'cultivation',
                              'msp', 'insurance']
        if any(keyword in query_lower for keyword in commercial_keywords):
            return ['commercial']
        
        # PRIORITY 13: Consumer (general)
        consumer_general = ['consumer', 'defective', 'refund']
        if any(keyword in query_lower for keyword in consumer_general):
            return ['consumer']
        
        # DEFAULT: Civil (safest fallback)
        return ['civil']
    
    def _build_augmented_search_context(self, query: str, understanding: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        understanding = understanding or {}

        search_queries = [query.strip()]
        for variant in understanding.get("search_queries", []):
            if isinstance(variant, str) and variant.strip():
                normalized = " ".join(variant.split())
                if normalized and normalized.lower() not in {q.lower() for q in search_queries}:
                    search_queries.append(normalized)

        query_terms = {word.lower() for word in query.split() if len(word) > 2}
        for keyword in understanding.get("keywords", []):
            if isinstance(keyword, str) and len(keyword.strip()) > 2:
                query_terms.add(keyword.strip().lower())
        for act_hint in understanding.get("act_hints", []):
            if isinstance(act_hint, str):
                for token in act_hint.replace("_", " ").split():
                    if len(token) > 2:
                        query_terms.add(token.lower())

        section_hints = {
            str(value).strip().lower()
            for value in understanding.get("section_hints", [])
            if str(value).strip()
        }
        act_hints = [
            str(value).strip().lower()
            for value in understanding.get("act_hints", [])
            if str(value).strip()
        ]

        return {
            "search_queries": search_queries[:5],
            "query_terms": query_terms,
            "section_hints": section_hints,
            "act_hints": act_hints,
            "matching_text": " ".join(search_queries).lower(),
        }

    def _search_relevant_sections(
        self,
        query: str,
        jurisdiction: str,
        domain: str,
        understanding: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[Section], Dict[str, Any]]:
        """Enhanced section search with optional Groq query understanding and reranking."""

        understanding = understanding or {}
        search_context = self._build_augmented_search_context(query, understanding)

        matched_sections = []
        query_lower = search_context["matching_text"]
        query_words = search_context["query_terms"]
        section_hints = search_context["section_hints"]
        act_hints = search_context["act_hints"]

        retrieval_metadata = {
            "search_queries": search_context["search_queries"],
            "understanding_source": understanding.get("source", "none"),
            "understanding_model": understanding.get("model"),
        }
        if understanding.get("disabled_reason"):
            retrieval_metadata["understanding_disabled_reason"] = understanding["disabled_reason"]
        if understanding.get("groq_error"):
            retrieval_metadata["understanding_error"] = understanding["groq_error"]

        if section_hints:
            for section in self.jurisdiction_sections.get(jurisdiction, []):
                section_number = section.section_number.lower()
                if any(hint == section_number or hint in section_number for hint in section_hints):
                    score = 220
                    if act_hints and any(act_hint in section.act_id.lower() for act_hint in act_hints):
                        score += 20
                    matched_sections.append((section, score))

        # Explicit mapping for false/false police complaint scenarios
        false_complaint_phrases = [
            "false complaint",
            "false police complaint",
            "false fir",
            "fake fir",
            "false case",
            "fake case",
            "false police case",
        ]
        if any(phrase in query_lower for phrase in false_complaint_phrases):
            for section in self.sections:
                if section.jurisdiction.value != jurisdiction:
                    continue
                if section.section_number in {"182", "211"}:
                    if any(tag in section.act_id.lower() for tag in ["ipc", "bns"]):
                        matched_sections.append((section, 200))

        crime_mapping_triggered = False
        if jurisdiction in self.crime_mappings:
            for crime, section_numbers in self.crime_mappings[jurisdiction].items():
                crime_words = crime.split('_')
                match_found = False

                if crime in query_lower:
                    match_found = True

                if not match_found:
                    for crime_word in crime_words:
                        if crime_word in query_lower:
                            match_found = True
                            break

                if not match_found:
                    for query_word in query_lower.split():
                        if len(query_word) > 3:
                            for crime_word in crime_words:
                                if len(crime_word) > 3 and query_word[:4] == crime_word[:4]:
                                    match_found = True
                                    break
                        if match_found:
                            break

                if match_found:
                    crime_mapping_triggered = True
                    for section in self.sections:
                        if section.jurisdiction.value != jurisdiction:
                            continue
                        section_matches = any(
                            mapped_num in section.section_number or section.section_number in mapped_num
                            for mapped_num in section_numbers
                        )
                        if not section_matches:
                            continue
                        if crime in ['accident', 'bike_accident', 'car_accident', 'road_accident', 'vehicle_accident',
                                     'drunk_driving', 'rash_driving', 'negligent_driving'] and 'bns' in section.act_id.lower():
                            continue
                        if crime in ['terrorism', 'terrorist_attack']:
                            if section.section_number == '113' and 'bns' in section.act_id.lower():
                                matched_sections.append((section, 200))
                            elif section.section_number == '66F' and 'it_act' in section.act_id.lower():
                                matched_sections.append((section, 195))
                            else:
                                matched_sections.append((section, 180))
                        elif crime in ['rape', 'sexual_assault', 'sexual_harassment']:
                            matched_sections.append((section, 190))
                        elif crime in ['cybercrime', 'hacking', 'identity_theft', 'cyber_terrorism']:
                            if 'it_act' in section.act_id.lower():
                                matched_sections.append((section, 180))
                            else:
                                matched_sections.append((section, 100))
                        else:
                            matched_sections.append((section, 150))

        bm25_scores = {}
        for index, search_query in enumerate(search_context["search_queries"]):
            weight = 1.0 if index == 0 else 0.7
            bm25_results = self.bm25_search.search(search_query, jurisdiction, top_k=50)
            for section, score in bm25_results:
                exclude_titles = ['accident in doing', 'lawful act', 'repeal', 'savings']
                if domain != 'civil':
                    exclude_titles.extend(['commencement', 'short title', 'definitions', 'extent', 'application'])
                if any(keyword in section.text.lower()[:80] for keyword in exclude_titles):
                    continue

                scaled_score = score * weight * (5 if not crime_mapping_triggered else 2)
                if act_hints and any(act_hint in section.act_id.lower() for act_hint in act_hints):
                    scaled_score *= 1.2

                if section.section_id not in bm25_scores or scaled_score > bm25_scores[section.section_id][1]:
                    bm25_scores[section.section_id] = (section, scaled_score)

        retrieval_metadata["bm25_queries_run"] = len(search_context["search_queries"])
        matched_sections.extend(bm25_scores.values())

        for word in query_words:
            if word in self.section_index:
                for section in self.section_index[word]:
                    if section.jurisdiction.value != jurisdiction:
                        continue
                    score = 0
                    section_text_lower = section.text.lower()
                    for query_word in query_words:
                        if query_word in section_text_lower:
                            score += 5
                    for query_word in query_words:
                        if any(query_word in token for token in section_text_lower.split()):
                            score += 2

                    domain_keywords = {
                        'criminal': ['offence', 'punishment', 'imprisonment', 'fine', 'criminal'],
                        'civil': ['damages', 'compensation', 'liability', 'breach', 'contract', 'tax', 'assessment', 'return', 'invoice', 'credit', 'salary', 'wages', 'builder', 'possession', 'rera'],
                        'family': ['marriage', 'divorce', 'custody', 'family', 'matrimonial'],
                        'commercial': ['company', 'business', 'commercial', 'trade', 'corporate']
                    }

                    if domain in domain_keywords:
                        for domain_word in domain_keywords[domain]:
                            if domain_word in section_text_lower:
                                score += 3

                    if act_hints and any(act_hint in section.act_id.lower() for act_hint in act_hints):
                        score += 10

                    if score > 0:
                        matched_sections.append((section, score))

        for section in self.jurisdiction_sections.get(jurisdiction, []):
            if hasattr(section, 'metadata') and section.metadata:
                metadata_text = str(section.metadata).lower()
                score = 0
                for word in query_words:
                    if word in metadata_text:
                        score += 4
                if act_hints and any(act_hint in section.act_id.lower() for act_hint in act_hints):
                    score += 6
                if score > 0:
                    matched_sections.append((section, score))

        unique_sections = {}
        for section, score in matched_sections:
            if score < 2:
                continue
            if section.section_id not in unique_sections or score > unique_sections[section.section_id][1]:
                unique_sections[section.section_id] = (section, score)

        sorted_sections = sorted(unique_sections.values(), key=lambda item: item[1], reverse=True)

        act_filters = [
            # Cybercrime -> IT Act
            {
                'keywords': ['hack', 'cyber', 'phishing', 'data breach', 'computer', 'online fraud', 'digital', 'internet', 'email', 'website', 'password', 'account', 'unauthorized access'],
                'acts': ['it_act'],
                'min_sections': 4
            },
            # Property -> Property Laws (check BEFORE agriculture)
            {
                'keywords': ['property', 'tenant', 'landlord', 'eviction', 'rent', 'lease', 'mortgage', 'rera', 'builder', 'building', 'flat', 'house', 'apartment', 'real estate', 'ownership', 'land dispute', 'boundary dispute', 'title deed', 'encroachment', 'possession', 'project', 'construction delay', 'delayed possession', 'not built', 'not completed', 'handover'],
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
                'keywords': ['salary', 'wages', 'fired', 'termination', 'boss', 'employer', 'employee', 'workplace', 'leave', 'overtime', 'gratuity', 'pf', 'epf', 'job', 'work', 'office', 'company', 'resignation', 'dismissal', 'harassment', 'not paying', 'unpaid', 'pending salary', 'payment of wages'],
                'acts': ['labour', 'employment'],
                'min_sections': 3
            },
            # Consumer -> Consumer Protection Act
            {
                'keywords': ['defective', 'product', 'refund', 'consumer', 'warranty', 'guarantee', 'shop', 'purchase', 'bought', 'seller', 'buyer', 'goods', 'service', 'complaint', 'quality'],
                'acts': ['consumer_protection'],
                'min_sections': 3
            },
            # Tax -> Income-tax Act / CGST Act
            {
                'keywords': ['income tax', 'tax evasion', 'tax avoidance', 'gst', 'cgst', 'igst', 'sgst', 'tds', 'input tax credit', 'itc', 'assessment', 'fake invoice', 'bogus invoice', 'refund fraud', 'under-reported income', 'misreported income'],
                'acts': ['income_tax', 'cgst_act', 'gst'],
                'min_sections': 2
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

        best_match = None
        best_score = 0

        if self.semantic_search:
            act_descriptions = {
                'it_act': 'cybercrime hacking computer internet digital fraud phishing data breach online security',
                'farmers_protection': 'farmer agriculture crop cultivation farming land irrigation seed fertilizer harvest',
                'labour': 'employment salary wages unpaid salary unpaid wages job work termination firing workplace employee employer payment of wages',
                'consumer_protection': 'consumer product defective refund warranty purchase goods service quality',
                'income_tax': 'income tax tax evasion tax avoidance under reported income misreported income tds gaar assessment return penalty prosecution',
                'cgst': 'gst cgst fake invoice bogus invoice input tax credit itc refund fraud tax evasion collected tax not paid',
                'property': 'property real estate tenant landlord rent lease mortgage house flat building builder delayed possession rera project completion refund interest',
                'motor_vehicles': 'vehicle car accident driving license insurance traffic road collision',
                'hindu_marriage': 'marriage divorce custody alimony spouse wife husband family matrimonial'
            }

            best_act = self.semantic_search.find_best_act(query, act_descriptions)
            if best_act:
                for filter_rule in act_filters:
                    if any(best_act in act for act in filter_rule['acts']):
                        best_match = filter_rule
                        best_score = 10
                        break

        if not best_match and act_hints:
            for filter_rule in act_filters:
                if any(any(act_hint in act for act in filter_rule['acts']) for act_hint in act_hints):
                    best_match = filter_rule
                    best_score = 8
                    break

        if not best_match:
            for filter_rule in act_filters:
                match_count = sum(1 for keyword in filter_rule['keywords'] if keyword in query_lower)
                if match_count > best_score:
                    best_score = match_count
                    best_match = filter_rule

        rerank_candidates = [section for section, _ in sorted_sections[:20]]
        if best_match and best_score >= 2:
            filtered_sections = [
                (s, score) for s, score in sorted_sections
                if any(act in s.act_id.lower() for act in best_match['acts'])
            ]
            if len(filtered_sections) >= best_match['min_sections']:
                rerank_candidates = [section for section, _ in filtered_sections[:20]]

        rerank_result = self.groq_retrieval_augmentor.rerank_sections(
            query=query,
            sections=rerank_candidates,
            jurisdiction=jurisdiction,
            domain=domain,
            understanding=understanding,
            top_k=10,
        )
        retrieval_metadata["rerank_source"] = rerank_result.get("source", "local")
        retrieval_metadata["rerank_model"] = rerank_result.get("model")
        retrieval_metadata["rerank_reason"] = rerank_result.get("reason", "")

        final_sections = rerank_result.get("sections") or [section for section, _ in sorted_sections[:10]]
        return final_sections[:10], retrieval_metadata
    
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

    @staticmethod
    def _normalize_section_number(section_number: Any) -> str:
        value = str(section_number or "").strip()
        return re.sub(r"^(section|article)[_\-\s]+", "", value, flags=re.IGNORECASE)

    def _match_query_statute_override(self, query_lower: str) -> Optional[List[Dict[str, Any]]]:
        for rule in QUERY_STATUTE_OVERRIDES:
            require_all = rule.get("all", [])
            require_any = rule.get("any", [])
            exclude = rule.get("exclude", [])
            if require_all and not all(term in query_lower for term in require_all):
                continue
            if require_any and not any(term in query_lower for term in require_any):
                continue
            if exclude and any(term in query_lower for term in exclude):
                continue
            return rule.get("statutes", [])
        return None

    def _augment_sections_from_full_db_search(
        self,
        query: str,
        jurisdiction: str,
        domain: str,
        sections: List[Section],
    ) -> List[Section]:
        if jurisdiction != 'IN' or domain != 'civil':
            return sections

        try:
            from legal_database.database_loader import legal_db
        except Exception:
            return sections

        db_results = legal_db.get_legal_sections(query, jurisdiction, domain, limit=5)
        if not db_results:
            return sections

        section_lookup = {}
        for section in self.sections:
            if section.jurisdiction.value != jurisdiction:
                continue
            key = (
                section.act_id,
                self._normalize_section_number(section.section_number),
            )
            section_lookup.setdefault(key, section)

        merged_sections = []
        seen = set()

        for item in db_results:
            key = (
                item.get("act_id", ""),
                self._normalize_section_number(item.get("section", "")),
            )
            section = section_lookup.get(key)
            if section and section.section_id not in seen:
                seen.add(section.section_id)
                merged_sections.append(section)

        for section in sections:
            if section.section_id not in seen:
                seen.add(section.section_id)
                merged_sections.append(section)

        return merged_sections
    
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
        section_text = " ".join(section.text.lower() for section in sections)
        act_text = " ".join((section.act_id or "").lower() for section in sections)

        def add_remedies(*items: str):
            for item in items:
                if item and item not in remedies:
                    remedies.append(item)
        
        # Check for specific offense types
        is_sexual_offence = any('375' in s.section_number or '376' in s.section_number or 
                               '63' in s.section_number or '64' in s.section_number or
                               'rape' in s.section_id.lower() for s in sections)
        
        is_serious_crime = any(word in s.text.lower() for s in sections 
                              for word in ['murder', 'homicide', 'terrorism', 'trafficking'])
        is_theft = any(word in query_lower or word in section_text for word in ['theft', 'stolen', 'steal', 'robbery', 'snatching', 'chain snatching'])
        is_assault = any(word in query_lower or word in section_text for word in ['assault', 'hurt', 'grievous hurt', 'beating', 'attack', 'violence'])
        is_cyber = any(word in query_lower or word in section_text or word in act_text for word in ['cyber', 'hacking', 'phishing', 'identity theft', 'data breach', 'it_act'])
        is_traffic = any(word in query_lower or word in section_text or word in act_text for word in ['accident', 'drunk driving', 'traffic', 'vehicle', 'rash driving', 'motor_vehicles'])
        is_property = any(word in query_lower or word in section_text or word in act_text for word in ['property', 'tenant', 'landlord', 'eviction', 'boundary', 'title', 'encroachment', 'land'])
        is_salary = any(word in query_lower or word in section_text or word in act_text for word in ['salary', 'wages', 'termination', 'gratuity', 'pf', 'provident fund', 'employee', 'employer', 'labour'])
        is_consumer = any(word in query_lower or word in section_text or word in act_text for word in ['consumer', 'defective', 'refund', 'warranty', 'replacement', 'deficiency'])
        is_medical = any(word in query_lower or word in section_text for word in ['medical negligence', 'doctor', 'hospital', 'malpractice', 'treatment'])
        is_domestic = any(word in query_lower or word in section_text for word in ['domestic violence', 'dowry', '498a', 'cruelty', 'husband', 'wife', 'protection order'])
        
        if is_sexual_offence:
            if jurisdiction == 'IN':
                add_remedies(
                    "Criminal prosecution with rigorous imprisonment (minimum 7 years, may extend to life)",
                    "Compensation under Section 357A CrPC (up to Rs.10 lakhs)",
                    "Free legal aid under Legal Services Authorities Act",
                    "Protection under Witness Protection Scheme",
                    "Medical treatment at government expense",
                    "Shelter and rehabilitation services",
                    "24/7 helpline support (1091 Women Helpline)"
                )
            elif jurisdiction == 'UK':
                add_remedies(
                    "Criminal prosecution with life imprisonment possible",
                    "Criminal Injuries Compensation Authority (CICA) claim",
                    "Special measures for vulnerable witnesses",
                    "Restraining orders and protection",
                    "NHS counseling and medical support"
                )
            elif jurisdiction == 'UAE':
                add_remedies(
                    "Criminal prosecution with severe penalties",
                    "Diya (blood money) compensation",
                    "Court-ordered compensation",
                    "Protection orders",
                    "Medical and psychological support"
                )
        
        elif is_serious_crime:
            if jurisdiction == 'IN':
                add_remedies(
                    "Criminal prosecution with life imprisonment/death penalty",
                    "Victim compensation under CrPC",
                    "Free legal aid",
                    "Witness protection",
                    "Appeal to higher courts"
                )
            else:
                add_remedies(
                    "Criminal prosecution with maximum penalties",
                    "Victim compensation schemes",
                    "Legal aid and support",
                    "Protection measures"
                )
        
        elif jurisdiction == 'IN' and is_domestic:
            add_remedies(
                "Criminal prosecution under applicable cruelty, dowry, assault, or intimidation provisions",
                "Protection orders, residence orders, and monetary relief under the Domestic Violence Act",
                "Maintenance and interim financial support where applicable",
                "Compensation for physical, emotional, and economic abuse",
                "Shelter access, police protection, and free legal aid"
            )
        
        elif jurisdiction == 'IN' and is_theft:
            add_remedies(
                "Criminal prosecution for theft, robbery, or related offences with imprisonment/fine as applicable",
                "Recovery or return of stolen property through police investigation and court process",
                "Victim compensation or restitution for financial loss where supported by the record",
                "Seizure, preservation, and release of recovered property by court order",
                "Free legal aid and victim support services if eligible"
            )
        
        elif jurisdiction == 'IN' and is_cyber:
            add_remedies(
                "Criminal prosecution under applicable IT Act, BNS, or IPC provisions",
                "Complaint before cybercrime police/cell and urgent preservation of digital evidence",
                "Freezing of bank accounts, wallets, SIMs, or devices used in the fraud where traceable",
                "Recovery, restitution, or compensation for financial loss where possible",
                "Platform, bank, or intermediary escalation to block further unauthorized activity"
            )
        
        elif jurisdiction == 'IN' and is_traffic:
            add_remedies(
                "Criminal prosecution for rash, negligent, dangerous, or intoxicated driving",
                "Motor accident compensation claim for injury, disability, death, or property loss",
                "Insurance claim for vehicle damage, treatment costs, and related losses",
                "Interim or final compensation for medical expenses and loss of income",
                "Compounding of minor traffic violations where legally permitted"
            )
        
        elif jurisdiction == 'IN' and is_assault:
            add_remedies(
                "Criminal prosecution for hurt, grievous hurt, intimidation, or related violent offences",
                "Immediate medical examination and injury documentation for prosecution and compensation",
                "Victim compensation under Section 357A CrPC where applicable",
                "Protection measures or police assistance if there is ongoing threat or intimidation",
                "Free legal aid and witness protection in serious cases"
            )
        
        else:
            # Extract remedies from section metadata
            for section in sections:
                if hasattr(section, 'metadata') and section.metadata:
                    if 'civil_remedies' in section.metadata:
                        section_remedies = section.metadata['civil_remedies']
                        if isinstance(section_remedies, list):
                            add_remedies(*[f"Legal: {remedy}" for remedy in section_remedies])
                        else:
                            add_remedies(f"Legal: {section_remedies}")
                    
                    if 'punishment' in section.metadata:
                        add_remedies(f"Criminal: {section.metadata['punishment']}")
            
            # Default remedies by domain if none found
            if not remedies:
                if domain == 'criminal':
                    if jurisdiction == 'IN':
                        add_remedies(
                            "Criminal prosecution and imprisonment/fine as per law",
                            "Victim compensation under Section 357A CrPC where applicable",
                            "Police investigation, seizure of evidence, and charge sheet/trial process",
                            "Bail objections or protective conditions in appropriate cases",
                            "Legal aid and victim support if eligible"
                        )
                    elif jurisdiction == 'UK':
                        add_remedies(
                            "Criminal prosecution and sentencing",
                            "Criminal Injuries Compensation",
                            "Protective measures and legal aid if eligible"
                        )
                    elif jurisdiction == 'UAE':
                        add_remedies(
                            "Criminal prosecution and penalties",
                            "Court-ordered compensation",
                            "Legal representation and protective orders where available"
                        )
                
                elif domain == 'civil':
                    if is_property:
                        add_remedies(
                            "Declaration of title, legal rights, or share in the property",
                            "Temporary or permanent injunction against dispossession, interference, or transfer",
                            "Recovery of possession, partition, demarcation, or mesne profits as applicable",
                            "Cancellation, rectification, or specific performance of property documents",
                            "Compensation for wrongful occupation, damage, or breach of property obligations"
                        )
                    elif is_medical:
                        add_remedies(
                            "Compensation for medical negligence, treatment costs, disability, or death",
                            "Consumer complaint for deficiency in medical service where maintainable",
                            "Professional disciplinary complaint before the medical regulator",
                            "Civil damages for pain, suffering, and loss of income",
                            "Criminal complaint in cases of gross negligence if supported by facts"
                        )
                    else:
                        add_remedies(
                            "Monetary damages and compensation",
                            "Specific performance of contract or legal obligation",
                            "Temporary or permanent injunctive relief",
                            "Restitution, restoration, or cancellation of offending acts/documents",
                            "Declaratory relief clarifying rights and liabilities"
                        )
                
                elif domain == 'family':
                    if jurisdiction == 'IN':
                        # Check if it's a divorce query
                        if any(word in query_lower for word in ['divorce', 'separation']):
                            add_remedies(
                                "Divorce decree under Hindu Marriage Act Section 13",
                                "Child custody and visitation rights under Section 26",
                                "Maintenance and alimony under Sections 25 & 27",
                                "Property settlement and division",
                                "Protection orders if domestic violence involved",
                                "One-time permanent alimony or monthly maintenance"
                            )
                        else:
                            add_remedies(
                                "Child custody and visitation rights",
                                "Maintenance and alimony",
                                "Property settlement",
                                "Protection orders if needed"
                            )
                    else:
                        add_remedies(
                            "Child arrangements orders",
                            "Financial settlements",
                            "Property division",
                            "Non-molestation orders"
                        )
                
                elif domain == 'commercial':
                    if is_salary:
                        add_remedies(
                            "Recovery of unpaid salary, wages, bonus, gratuity, or other service dues",
                            "Complaint before labour authority, labour commissioner, or competent employment forum",
                            "Reinstatement, back wages, or compensation for wrongful termination where applicable",
                            "Provident fund, gratuity, and statutory benefit recovery",
                            "Conciliation, settlement, or adjudication of the employment dispute"
                        )
                    elif is_consumer:
                        add_remedies(
                            "Refund, replacement, repair, or removal of defects in goods/services",
                            "Compensation for deficiency in service, unfair trade practice, or consequential loss",
                            "Consumer complaint before the appropriate commission/forum",
                            "Litigation costs and interest on the consumer claim",
                            "Directions to discontinue misleading or unsafe practices"
                        )
                    else:
                        add_remedies(
                            "Breach of contract damages",
                            "Specific performance",
                            "Injunctive relief",
                            "Rescission and restitution",
                            "Account of profits"
                        )

                elif domain == 'consumer':
                    add_remedies(
                        "Refund, replacement, repair, or removal of defects in goods/services",
                        "Compensation for deficiency in service, overcharging, or unfair trade practice",
                        "Consumer complaint before the appropriate commission/forum",
                        "Interest, litigation costs, and corrective directions against the seller/service provider",
                        "Product recall, discontinuance, or other compliance directions where justified"
                    )
        
        return remedies[:10]
    
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
        query_understanding = self.groq_retrieval_augmentor.understand_query(
            query=legal_query.query_text,
            jurisdiction_hint=legal_query.jurisdiction_hint,
            domain_hint=legal_query.domain_hint,
        )

        # Log classification
        self._log_enforcement_event("jurisdiction_resolved", trace_id, {
            "jurisdiction": jurisdiction,
            "domain": domain,
            "domains": domains,
            "available_jurisdictions": list(self.jurisdiction_sections.keys()),
            "total_sections": len(self.sections)
        })
        
        # Search relevant sections
        relevant_sections, retrieval_metadata = self._search_relevant_sections(
            legal_query.query_text,
            jurisdiction,
            domain,
            query_understanding,
        )

        # Remove helper routing/domain-map placeholders
        relevant_sections = [
            section for section in relevant_sections
            if "domain_map" not in str(section.act_id).lower()
            and "routes" not in str(section.act_id).lower()
        ]

        # Augment with full database search for Indian civil matters (captures tax/property/employment statutes)
        augmented_sections = self._augment_sections_from_full_db_search(
            legal_query.query_text,
            jurisdiction,
            domain,
            relevant_sections,
        )
        if len(augmented_sections) != len(relevant_sections):
            retrieval_metadata["full_db_augmented"] = {
                "before": len(relevant_sections),
                "after": len(augmented_sections),
            }
        relevant_sections = augmented_sections
        
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
            "remedies_count": len(remedies),
            "retrieval_metadata": retrieval_metadata,
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
                
                # Enhanced title for rape sections (India only - BNS/IPC sections)
                enhanced_title = completed.get('title', completed['act'])
                section_num = completed['section']
                
                # Only apply enhanced titles for Indian rape sections
                if jurisdiction == 'IN' and section_num in ['63', '64', '65', '66', '375', '376', '376A', '376AB', '376B', '376C', '376D']:
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
                
                # Apply enhanced titles for Indian divorce sections from addon
                if jurisdiction == 'IN' and section_num in ['13', '13B', '24', '25', '27']:
                    if section_num == '13':
                        enhanced_title = "Divorce - Grounds including adultery, cruelty, desertion, conversion, mental disorder (Hindu Marriage Act 1955)"
                    elif section_num == '13B':
                        enhanced_title = "Divorce by mutual consent - Both parties agree to dissolve marriage after 1 year separation"
                    elif section_num == '24':
                        enhanced_title = "Maintenance pendente lite - Interim maintenance during divorce proceedings"
                    elif section_num == '25':
                        enhanced_title = "Permanent alimony - Court may order maintenance after divorce"
                    elif section_num == '27':
                        enhanced_title = "Divorce - Grounds including adultery, cruelty, desertion, unsound mind (Special Marriage Act 1954)"
                
                addon_statutes.append({
                    'act': completed['act'],
                    'year': completed.get('year', 0),
                    'section': completed['section'],
                    'title': enhanced_title
                })
            
            # Apply offense subtype prioritization for rape-related addons
            if 'rape' in addon_subtype:
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
            # Skip sections that don't match the detected jurisdiction
            if section.jurisdiction.value != jurisdiction:
                continue
            
            act_id_lower = section.act_id.lower() if section.act_id else ''
            act_metadata = None
            
            # Find matching act metadata
            for act_key, metadata in ACT_METADATA.items():
                if act_key.lower() in act_id_lower or act_id_lower in act_key.lower():
                    act_metadata = metadata
                    break
            
            # Enhanced title for rape sections (India only - BNS/IPC sections)
            enhanced_title = section.text[:100] if len(section.text) > 100 else section.text
            
            # Add detailed description for Indian rape sections only
            if jurisdiction == 'IN' and section.section_number in ['63', '64', '65', '66', '375', '376', '376A', '376AB', '376B', '376C', '376D']:
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
            
            # Add detailed description for Indian divorce sections
            if jurisdiction == 'IN' and section.section_number in ['13', '13B', '24', '25', '27']:
                if section.section_number == '13' and 'hindu_marriage' in section.act_id.lower():
                    enhanced_title = "Divorce - Grounds including adultery, cruelty, desertion, conversion, mental disorder (Hindu Marriage Act 1955)"
                elif section.section_number == '13B' and 'hindu_marriage' in section.act_id.lower():
                    enhanced_title = "Divorce by mutual consent - Both parties agree to dissolve marriage after 1 year separation"
                elif section.section_number == '24' and 'hindu_marriage' in section.act_id.lower():
                    enhanced_title = "Maintenance pendente lite - Interim maintenance during divorce proceedings"
                elif section.section_number == '25' and 'hindu_marriage' in section.act_id.lower():
                    enhanced_title = "Permanent alimony - Court may order maintenance after divorce"
                elif section.section_number == '27' and 'special_marriage' in section.act_id.lower():
                    enhanced_title = "Divorce - Grounds including adultery, cruelty, desertion, unsound mind (Special Marriage Act 1954)"
            
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
        deduped_statutes = []
        seen_statutes = set()
        for statute in all_statutes:
            key = (
                statute.get('act'),
                statute.get('year'),
                statute.get('section'),
                statute.get('title')
            )
            if key in seen_statutes:
                continue
            seen_statutes.add(key)
            deduped_statutes.append(statute)
        all_statutes = deduped_statutes

        section_hints = {
            str(value).strip().lower()
            for value in query_understanding.get("section_hints", [])
            if str(value).strip()
        }
        act_hints = {
            str(value).strip().lower()
            for value in query_understanding.get("act_hints", [])
            if str(value).strip()
        }

        def statute_priority(statute: Dict[str, Any]) -> int:
            score = 0
            section_number = str(statute.get('section', '')).lower()
            act_name = str(statute.get('act', '')).lower().replace(' ', '_')
            title = str(statute.get('title', '')).lower()
            query_text_lower = legal_query.query_text.lower()

            if any(hint == section_number or hint in section_number for hint in section_hints):
                score += 100
            if any(act_hint in act_name for act_hint in act_hints):
                score += 35
            if 'punishment' in query_text_lower and 'punishment' in title:
                score += 20
            if any(token in title for token in query_text_lower.split() if len(token) > 3):
                score += 5
            return score

        all_statutes.sort(key=statute_priority, reverse=True)

        # Filter statutes by jurisdiction - remove Indian acts for non-Indian jurisdictions
        indian_acts = ['Hindu Marriage Act', 'Special Marriage Act', 'Bharatiya Nyaya Sanhita', 'Indian Penal Code', 
                       'Code of Criminal Procedure', 'Code of Civil Procedure', 'Indian Evidence Act',
                       'Information Technology Act', 'Protection of Women from Domestic Violence Act',
                       'Dowry Prohibition Act', 'Consumer Protection Act', 'Income-tax Act',
                       'Central Goods and Services Tax Act', 'Motor Vehicles Act',
                       'Unlawful Activities (Prevention) Act', 'Labour and Employment Laws',
                       'Real Estate (Regulation and Development) Act', 'Farmers Protection Act']
        
        if jurisdiction != 'IN':
            all_statutes = [s for s in all_statutes if s.get('act') not in indian_acts]
        elif jurisdiction == 'IN':
            # For India, remove UK/UAE specific acts
            uk_uae_acts = ['Sexual Offences Act', 'Theft Act', 'Fraud Act', 'Road Traffic Act',
                          'UAE Penal Code', 'UAE Personal Status Law', 'UAE Traffic Law', 'UAE Cybercrime Law']
            all_statutes = [s for s in all_statutes if s.get('act') not in uk_uae_acts]
        
        all_statutes, dowry_filtered = self.dowry_precision.filter_and_prioritize(all_statutes, legal_query.query_text)
        
        # Boost confidence for dowry cases
        if dowry_filtered:
            confidence_score = self.dowry_precision.boost_confidence(all_statutes)
            ontology_filtered = True
        
        # Check for land dispute queries and use predefined statutes (India only)
        query_lower = legal_query.query_text.lower()
        if jurisdiction == 'IN' and any(keyword in query_lower for keyword in ['land dispute', 'property dispute', 'land', 'boundary', 'title deed', 'encroachment']):
            all_statutes = LAND_DISPUTE_STATUTES.copy()

        override_statutes = self._match_query_statute_override(query_lower)
        if jurisdiction == 'IN' and override_statutes:
            all_statutes = override_statutes
        
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
            ontology_filtered=ontology_filtered or dowry_filtered,
            query_understanding=query_understanding,
            retrieval_metadata=retrieval_metadata,
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
