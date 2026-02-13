#!/usr/bin/env python3
"""
Comprehensive Query Analyzer
Uses both main database (1,693 sections) and procedure datasets
"""
import json
import os
from typing import Dict, List, Any, Tuple

class ComprehensiveQueryAnalyzer:
    def __init__(self):
        self.main_db = {}
        self.procedure_db = {}
        self.load_databases()
        
    def load_databases(self):
        """Load both main database and procedure datasets"""
        print("Loading comprehensive legal databases...")
        
        # Load main database (db folder)
        db_path = "db"
        for filename in os.listdir(db_path):
            if filename.endswith('.json'):
                filepath = os.path.join(db_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.main_db[filename] = json.load(f)
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        # Load procedure datasets
        proc_path = "../nyaya-legal-procedure-datasets/data/procedures"
        if os.path.exists(proc_path):
            for jurisdiction in ['india', 'uk', 'uae', 'ksa']:
                jurisdiction_path = os.path.join(proc_path, jurisdiction)
                if os.path.exists(jurisdiction_path):
                    self.procedure_db[jurisdiction] = {}
                    for domain_file in os.listdir(jurisdiction_path):
                        if domain_file.endswith('.json'):
                            domain = domain_file.replace('.json', '')
                            filepath = os.path.join(jurisdiction_path, domain_file)
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    self.procedure_db[jurisdiction][domain] = json.load(f)
                            except Exception as e:
                                print(f"Error loading {jurisdiction}/{domain}: {e}")
        
        print(f"Loaded {len(self.main_db)} main database files")
        print(f"Loaded procedures for {len(self.procedure_db)} jurisdictions")
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Comprehensive query analysis using both datasets"""
        result = {
            "query": query,
            "main_db_matches": self.search_main_database(query),
            "procedure_matches": self.search_procedures(query),
            "comprehensive_analysis": {},
            "recommendations": []
        }
        
        # Generate comprehensive analysis
        result["comprehensive_analysis"] = self.generate_analysis(
            query, result["main_db_matches"], result["procedure_matches"]
        )
        
        return result
    
    def search_main_database(self, query: str) -> Dict[str, Any]:
        """Search the main legal database (1,693 sections)"""
        matches = {
            "total_sections_found": 0,
            "by_jurisdiction": {},
            "relevant_sections": [],
            "acts_involved": set()
        }
        
        query_lower = query.lower()
        keywords = set(word.lower() for word in query.split() if len(word) > 2)
        
        # Search through main database
        for filename, data in self.main_db.items():
            file_matches = self.search_file_content(filename, data, keywords, query_lower)
            if file_matches["sections"]:
                jurisdiction = self.detect_jurisdiction_from_filename(filename)
                if jurisdiction not in matches["by_jurisdiction"]:
                    matches["by_jurisdiction"][jurisdiction] = []
                
                matches["by_jurisdiction"][jurisdiction].extend(file_matches["sections"])
                matches["relevant_sections"].extend(file_matches["sections"])
                matches["acts_involved"].update(file_matches["acts"])
                matches["total_sections_found"] += len(file_matches["sections"])
        
        matches["acts_involved"] = list(matches["acts_involved"])
        return matches
    
    def search_file_content(self, filename: str, data: Any, keywords: set, query_lower: str) -> Dict[str, Any]:
        """Search content within a single file"""
        matches = {"sections": [], "acts": set()}
        
        if isinstance(data, dict):
            # Handle different structures
            if "key_sections" in data:  # IPC structure
                for category, sections in data["key_sections"].items():
                    if isinstance(sections, dict):
                        for section_num, section_text in sections.items():
                            if self.is_relevant_section(section_text, keywords, query_lower):
                                matches["sections"].append({
                                    "section_number": section_num,
                                    "text": section_text,
                                    "category": category,
                                    "act": "IPC",
                                    "file": filename
                                })
                                matches["acts"].add("IPC")
            
            elif "structure" in data:  # BNS structure
                for category, sections in data["structure"].items():
                    if isinstance(sections, dict):
                        for section_num, section_text in sections.items():
                            if self.is_relevant_section(section_text, keywords, query_lower):
                                matches["sections"].append({
                                    "section_number": section_num,
                                    "text": section_text,
                                    "category": category,
                                    "act": "BNS",
                                    "file": filename
                                })
                                matches["acts"].add("BNS")
            
            else:
                # Handle other structures
                for key, value in data.items():
                    if isinstance(value, dict):
                        for section_num, section_text in value.items():
                            if isinstance(section_text, str) and self.is_relevant_section(section_text, keywords, query_lower):
                                matches["sections"].append({
                                    "section_number": section_num,
                                    "text": section_text,
                                    "category": key,
                                    "act": key,
                                    "file": filename
                                })
                                matches["acts"].add(key)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict) and "text" in item:
                                if self.is_relevant_section(item["text"], keywords, query_lower):
                                    matches["sections"].append({
                                        "section_number": item.get("section_number", "N/A"),
                                        "text": item["text"],
                                        "category": key,
                                        "act": key,
                                        "file": filename
                                    })
                                    matches["acts"].add(key)
        
        return matches
    
    def is_relevant_section(self, section_text: Any, keywords: set, query_lower: str) -> bool:
        """Check if a section is relevant to the query"""
        if not isinstance(section_text, str):
            return False
            
        section_lower = section_text.lower()
        
        # Direct keyword matches
        keyword_matches = sum(1 for keyword in keywords if keyword in section_lower)
        if keyword_matches >= 2:
            return True
        
        # Specific crime/legal term matches
        crime_terms = ['rape', 'murder', 'theft', 'assault', 'kidnapping', 'dowry', 'divorce', 'marriage', 'harassment']
        for term in crime_terms:
            if term in query_lower and term in section_lower:
                return True
        
        return False
    
    def search_procedures(self, query: str) -> Dict[str, Any]:
        """Search procedure datasets"""
        matches = {
            "procedures_found": 0,
            "by_jurisdiction": {},
            "relevant_procedures": []
        }
        
        query_lower = query.lower()
        
        for jurisdiction, domains in self.procedure_db.items():
            for domain, procedures in domains.items():
                if isinstance(procedures, dict):
                    relevant_procs = self.find_relevant_procedures(procedures, query_lower, jurisdiction, domain)
                    if relevant_procs:
                        if jurisdiction not in matches["by_jurisdiction"]:
                            matches["by_jurisdiction"][jurisdiction] = {}
                        matches["by_jurisdiction"][jurisdiction][domain] = relevant_procs
                        matches["relevant_procedures"].extend(relevant_procs)
                        matches["procedures_found"] += len(relevant_procs)
        
        return matches
    
    def find_relevant_procedures(self, procedures: Dict, query_lower: str, jurisdiction: str, domain: str) -> List[Dict]:
        """Find relevant procedures in a domain"""
        relevant = []
        
        if "procedure" in procedures and "steps" in procedures["procedure"]:
            # Check if query matches domain or procedure steps
            domain_match = domain.lower() in query_lower
            
            # Check steps for relevance
            relevant_steps = []
            for step in procedures["procedure"]["steps"]:
                step_text = f"{step.get('title', '')} {step.get('description', '')}".lower()
                if any(word in step_text for word in query_lower.split() if len(word) > 3):
                    relevant_steps.append({
                        "step": step.get("step", 0),
                        "title": step.get("title", ""),
                        "description": step.get("description", ""),
                        "actor": step.get("actor", "")
                    })
            
            if domain_match or relevant_steps:
                relevant.append({
                    "name": f"{jurisdiction.title()} {domain.title()} Procedure",
                    "description": f"Legal procedure for {domain} matters in {jurisdiction}",
                    "jurisdiction": jurisdiction,
                    "domain": domain,
                    "steps": relevant_steps if relevant_steps else procedures["procedure"]["steps"][:5],
                    "timelines": procedures["procedure"].get("timelines", {}),
                    "documents_required": procedures["procedure"].get("documents_required", [])
                })
        
        return relevant
    
    def detect_jurisdiction_from_filename(self, filename: str) -> str:
        """Detect jurisdiction from filename"""
        filename_lower = filename.lower()
        if any(x in filename_lower for x in ['ipc', 'bns', 'crpc', 'cpc', 'india']):
            return "India"
        elif any(x in filename_lower for x in ['uk', 'britain']):
            return "UK"
        elif any(x in filename_lower for x in ['uae', 'emirates']):
            return "UAE"
        return "Unknown"
    
    def generate_analysis(self, query: str, main_matches: Dict, proc_matches: Dict) -> Dict[str, Any]:
        """Generate comprehensive analysis"""
        analysis = {
            "query_classification": self.classify_query(query),
            "database_coverage": {
                "main_sections": main_matches["total_sections_found"],
                "procedures": proc_matches["procedures_found"],
                "jurisdictions_covered": list(set(
                    list(main_matches["by_jurisdiction"].keys()) + 
                    list(proc_matches["by_jurisdiction"].keys())
                ))
            },
            "confidence_score": self.calculate_confidence(main_matches, proc_matches),
            "primary_jurisdiction": self.determine_primary_jurisdiction(main_matches, proc_matches),
            "legal_domain": self.determine_legal_domain(query, main_matches)
        }
        
        return analysis
    
    def classify_query(self, query: str) -> str:
        """Classify the type of legal query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['rape', 'murder', 'theft', 'assault', 'kidnapping']):
            return "Criminal Law"
        elif any(word in query_lower for word in ['divorce', 'marriage', 'custody', 'family']):
            return "Family Law"
        elif any(word in query_lower for word in ['contract', 'property', 'civil', 'damages']):
            return "Civil Law"
        elif any(word in query_lower for word in ['company', 'business', 'commercial']):
            return "Commercial Law"
        else:
            return "General Legal"
    
    def calculate_confidence(self, main_matches: Dict, proc_matches: Dict) -> float:
        """Calculate confidence score based on matches"""
        base_score = 0.1
        
        # Main database contribution
        if main_matches["total_sections_found"] > 0:
            base_score += min(0.6, main_matches["total_sections_found"] * 0.05)
        
        # Procedure database contribution
        if proc_matches["procedures_found"] > 0:
            base_score += min(0.3, proc_matches["procedures_found"] * 0.1)
        
        return min(0.95, base_score)
    
    def determine_primary_jurisdiction(self, main_matches: Dict, proc_matches: Dict) -> str:
        """Determine the primary jurisdiction for the query"""
        jurisdiction_scores = {}
        
        # Score from main database
        for jurisdiction, sections in main_matches["by_jurisdiction"].items():
            jurisdiction_scores[jurisdiction] = len(sections)
        
        # Score from procedures
        for jurisdiction in proc_matches["by_jurisdiction"].keys():
            jurisdiction_scores[jurisdiction] = jurisdiction_scores.get(jurisdiction, 0) + 5
        
        if jurisdiction_scores:
            return max(jurisdiction_scores, key=jurisdiction_scores.get)
        return "India"  # Default
    
    def determine_legal_domain(self, query: str, main_matches: Dict) -> str:
        """Determine the legal domain"""
        query_lower = query.lower()
        
        # Check sections for domain indicators
        criminal_indicators = 0
        civil_indicators = 0
        family_indicators = 0
        
        for section in main_matches["relevant_sections"]:
            section_text = section["text"].lower()
            if any(word in section_text for word in ['punishment', 'imprisonment', 'fine', 'offence']):
                criminal_indicators += 1
            elif any(word in section_text for word in ['damages', 'compensation', 'contract']):
                civil_indicators += 1
            elif any(word in section_text for word in ['marriage', 'divorce', 'family']):
                family_indicators += 1
        
        if criminal_indicators > civil_indicators and criminal_indicators > family_indicators:
            return "Criminal"
        elif family_indicators > civil_indicators:
            return "Family"
        elif civil_indicators > 0:
            return "Civil"
        else:
            return self.classify_query(query).replace(" Law", "")

def test_comprehensive_analyzer():
    """Test the comprehensive analyzer with sample queries"""
    analyzer = ComprehensiveQueryAnalyzer()
    
    test_queries = [
        "What is the punishment for rape in India?",
        "How to file for divorce in India?",
        "Theft penalties under Indian law",
        "Dowry harassment case procedures",
        "Contract breach remedies in UAE"
    ]
    
    print("\n" + "="*80)
    print("COMPREHENSIVE QUERY ANALYSIS RESULTS")
    print("="*80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. QUERY: {query}")
        print("-" * 60)
        
        result = analyzer.analyze_query(query)
        
        # Main database results
        main_matches = result["main_db_matches"]
        print(f"Main Database: {main_matches['total_sections_found']} sections found")
        print(f"Acts Involved: {', '.join(main_matches['acts_involved'][:5])}")
        
        # Procedure results
        proc_matches = result["procedure_matches"]
        print(f"Procedures: {proc_matches['procedures_found']} procedures found")
        
        # Analysis
        analysis = result["comprehensive_analysis"]
        print(f"Classification: {analysis['query_classification']}")
        print(f"Primary Jurisdiction: {analysis['primary_jurisdiction']}")
        print(f"Legal Domain: {analysis['legal_domain']}")
        print(f"Confidence Score: {analysis['confidence_score']:.2f}")
        
        # Show top sections
        if main_matches["relevant_sections"]:
            print(f"Top Relevant Sections:")
            for section in main_matches["relevant_sections"][:3]:
                print(f"  - Section {section['section_number']} ({section['act']}): {section['text'][:80]}...")

if __name__ == "__main__":
    test_comprehensive_analyzer()