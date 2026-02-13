#!/usr/bin/env python3
"""
Enhanced Legal Query Analyzer
Uses comprehensive database (1,693 sections + procedures) for accurate legal analysis
"""
import json
import os
from typing import Dict, List, Any

class EnhancedLegalQueryAnalyzer:
    def __init__(self):
        self.main_db = {}
        self.procedure_db = {}
        self.load_databases()
        
    def load_databases(self):
        """Load both main database and procedure datasets"""
        # Load main database (1,693 sections)
        db_path = "db"
        for filename in os.listdir(db_path):
            if filename.endswith('.json'):
                filepath = os.path.join(db_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.main_db[filename] = json.load(f)
                except Exception as e:
                    continue
        
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
                                continue
    
    def analyze_legal_query(self, query: str) -> Dict[str, Any]:
        """Comprehensive legal query analysis"""
        # Search main database for relevant sections
        main_results = self.search_legal_sections(query)
        
        # Search procedure database
        procedure_results = self.search_procedures(query)
        
        # Generate comprehensive analysis
        analysis = {
            "query": query,
            "legal_sections": main_results,
            "procedures": procedure_results,
            "analysis": self.generate_legal_analysis(query, main_results, procedure_results),
            "recommendations": self.generate_recommendations(query, main_results, procedure_results)
        }
        
        return analysis
    
    def search_legal_sections(self, query: str) -> Dict[str, Any]:
        """Search 1,693 legal sections for relevant matches"""
        results = {
            "total_sections": 0,
            "relevant_sections": [],
            "by_act": {},
            "by_jurisdiction": {}
        }
        
        query_lower = query.lower()
        keywords = set(word.lower() for word in query.split() if len(word) > 2)
        
        # Crime-specific mappings for better accuracy
        crime_mappings = {
            'rape': ['63', '64', '65', '66', '375', '376'],
            'murder': ['100', '101', '103', '299', '300', '302'],
            'theft': ['303', '304', '378', '379', '380'],
            'dowry': ['80', '304B', '498A'],
            'divorce': ['13', '82', '83'],
            'harassment': ['75', '354A', '509']
        }
        
        # Direct crime mapping
        for crime, sections in crime_mappings.items():
            if crime in query_lower:
                results["relevant_sections"].extend(self.find_sections_by_numbers(sections, crime))
        
        # Keyword-based search through all files
        for filename, data in self.main_db.items():
            file_sections = self.extract_sections_from_file(filename, data, keywords, query_lower)
            results["relevant_sections"].extend(file_sections)
        
        # Remove duplicates and organize
        unique_sections = {}
        for section in results["relevant_sections"]:
            key = f"{section['act']}_{section['section_number']}"
            if key not in unique_sections:
                unique_sections[key] = section
        
        results["relevant_sections"] = list(unique_sections.values())
        results["total_sections"] = len(results["relevant_sections"])
        
        # Organize by act and jurisdiction
        for section in results["relevant_sections"]:
            act = section["act"]
            jurisdiction = section.get("jurisdiction", "India")
            
            if act not in results["by_act"]:
                results["by_act"][act] = []
            results["by_act"][act].append(section)
            
            if jurisdiction not in results["by_jurisdiction"]:
                results["by_jurisdiction"][jurisdiction] = []
            results["by_jurisdiction"][jurisdiction].append(section)
        
        return results
    
    def find_sections_by_numbers(self, section_numbers: List[str], crime_type: str) -> List[Dict]:
        """Find specific sections by their numbers"""
        found_sections = []
        
        for filename, data in self.main_db.items():
            if isinstance(data, dict):
                # Search in IPC structure
                if "key_sections" in data:
                    for category, sections in data["key_sections"].items():
                        if isinstance(sections, dict):
                            for num, text in sections.items():
                                if num in section_numbers:
                                    found_sections.append({
                                        "section_number": num,
                                        "text": text,
                                        "act": "IPC",
                                        "category": category,
                                        "jurisdiction": "India",
                                        "relevance": "Direct match",
                                        "crime_type": crime_type
                                    })
                
                # Search in BNS structure
                elif "structure" in data:
                    for category, sections in data["structure"].items():
                        if isinstance(sections, dict):
                            for num, text in sections.items():
                                if num in section_numbers:
                                    found_sections.append({
                                        "section_number": num,
                                        "text": text,
                                        "act": "BNS",
                                        "category": category,
                                        "jurisdiction": "India",
                                        "relevance": "Direct match",
                                        "crime_type": crime_type
                                    })
        
        return found_sections
    
    def extract_sections_from_file(self, filename: str, data: Any, keywords: set, query_lower: str) -> List[Dict]:
        """Extract relevant sections from a file"""
        sections = []
        
        if isinstance(data, dict):
            if "key_sections" in data:  # IPC
                for category, category_sections in data["key_sections"].items():
                    if isinstance(category_sections, dict):
                        for num, text in category_sections.items():
                            if isinstance(text, str) and self.is_section_relevant(text, keywords, query_lower):
                                sections.append({
                                    "section_number": num,
                                    "text": text,
                                    "act": "IPC",
                                    "category": category,
                                    "jurisdiction": "India",
                                    "file": filename
                                })
            
            elif "structure" in data:  # BNS
                for category, category_sections in data["structure"].items():
                    if isinstance(category_sections, dict):
                        for num, text in category_sections.items():
                            if isinstance(text, str) and self.is_section_relevant(text, keywords, query_lower):
                                sections.append({
                                    "section_number": num,
                                    "text": text,
                                    "act": "BNS",
                                    "category": category,
                                    "jurisdiction": "India",
                                    "file": filename
                                })
        
        return sections
    
    def is_section_relevant(self, text: str, keywords: set, query_lower: str) -> bool:
        """Check if a section is relevant to the query"""
        text_lower = text.lower()
        
        # High-priority terms
        priority_terms = ['rape', 'murder', 'theft', 'assault', 'dowry', 'divorce', 'harassment']
        for term in priority_terms:
            if term in query_lower and term in text_lower:
                return True
        
        # Keyword matching
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        return matches >= 2
    
    def search_procedures(self, query: str) -> Dict[str, Any]:
        """Search procedure datasets"""
        results = {
            "total_procedures": 0,
            "relevant_procedures": [],
            "by_jurisdiction": {}
        }
        
        query_lower = query.lower()
        
        for jurisdiction, domains in self.procedure_db.items():
            for domain, procedure_data in domains.items():
                if self.is_procedure_relevant(procedure_data, query_lower, domain):
                    proc_info = self.extract_procedure_info(procedure_data, jurisdiction, domain)
                    results["relevant_procedures"].append(proc_info)
                    
                    if jurisdiction not in results["by_jurisdiction"]:
                        results["by_jurisdiction"][jurisdiction] = []
                    results["by_jurisdiction"][jurisdiction].append(proc_info)
        
        results["total_procedures"] = len(results["relevant_procedures"])
        return results
    
    def is_procedure_relevant(self, procedure_data: Dict, query_lower: str, domain: str) -> bool:
        """Check if a procedure is relevant"""
        # Domain match
        if domain.lower() in query_lower:
            return True
        
        # Check procedure steps
        if "procedure" in procedure_data and "steps" in procedure_data["procedure"]:
            for step in procedure_data["procedure"]["steps"]:
                step_text = f"{step.get('title', '')} {step.get('description', '')}".lower()
                if any(word in step_text for word in query_lower.split() if len(word) > 3):
                    return True
        
        return False
    
    def extract_procedure_info(self, procedure_data: Dict, jurisdiction: str, domain: str) -> Dict:
        """Extract procedure information"""
        proc = procedure_data.get("procedure", {})
        return {
            "jurisdiction": jurisdiction.title(),
            "domain": domain.title(),
            "steps": len(proc.get("steps", [])),
            "timelines": proc.get("timelines", {}),
            "documents": proc.get("documents_required", []),
            "authorities": proc.get("authority", []),
            "key_steps": [step.get("title", "") for step in proc.get("steps", [])[:5]]
        }
    
    def generate_legal_analysis(self, query: str, main_results: Dict, procedure_results: Dict) -> Dict[str, Any]:
        """Generate comprehensive legal analysis"""
        return {
            "query_type": self.classify_query_type(query),
            "primary_jurisdiction": self.determine_jurisdiction(main_results, procedure_results),
            "legal_domain": self.determine_domain(query, main_results),
            "confidence_score": self.calculate_confidence(main_results, procedure_results),
            "complexity": self.assess_complexity(main_results, procedure_results),
            "key_findings": self.extract_key_findings(main_results, procedure_results)
        }
    
    def classify_query_type(self, query: str) -> str:
        """Classify the type of legal query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['punishment', 'penalty', 'sentence']):
            return "Penalty Inquiry"
        elif any(word in query_lower for word in ['procedure', 'process', 'file', 'steps']):
            return "Procedural Inquiry"
        elif any(word in query_lower for word in ['rights', 'remedies', 'compensation']):
            return "Rights & Remedies"
        else:
            return "General Legal Query"
    
    def determine_jurisdiction(self, main_results: Dict, procedure_results: Dict) -> str:
        """Determine primary jurisdiction"""
        # Count sections by jurisdiction
        jurisdiction_scores = {}
        
        for jurisdiction, sections in main_results["by_jurisdiction"].items():
            jurisdiction_scores[jurisdiction] = len(sections)
        
        for jurisdiction, procedures in procedure_results["by_jurisdiction"].items():
            jurisdiction_scores[jurisdiction.title()] = jurisdiction_scores.get(jurisdiction.title(), 0) + len(procedures) * 2
        
        return max(jurisdiction_scores, key=jurisdiction_scores.get) if jurisdiction_scores else "India"
    
    def determine_domain(self, query: str, main_results: Dict) -> str:
        """Determine legal domain"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['rape', 'murder', 'theft', 'assault', 'criminal']):
            return "Criminal Law"
        elif any(word in query_lower for word in ['divorce', 'marriage', 'family', 'custody']):
            return "Family Law"
        elif any(word in query_lower for word in ['contract', 'property', 'civil', 'tort']):
            return "Civil Law"
        else:
            return "General Law"
    
    def calculate_confidence(self, main_results: Dict, procedure_results: Dict) -> float:
        """Calculate confidence score"""
        base_score = 0.1
        
        # Main database contribution
        sections_found = main_results["total_sections"]
        if sections_found > 0:
            base_score += min(0.6, sections_found * 0.03)
        
        # Procedure contribution
        procedures_found = procedure_results["total_procedures"]
        if procedures_found > 0:
            base_score += min(0.3, procedures_found * 0.1)
        
        return min(0.95, base_score)
    
    def assess_complexity(self, main_results: Dict, procedure_results: Dict) -> str:
        """Assess case complexity"""
        total_elements = main_results["total_sections"] + procedure_results["total_procedures"]
        
        if total_elements >= 20:
            return "High"
        elif total_elements >= 10:
            return "Medium"
        else:
            return "Low"
    
    def extract_key_findings(self, main_results: Dict, procedure_results: Dict) -> List[str]:
        """Extract key findings"""
        findings = []
        
        if main_results["total_sections"] > 0:
            findings.append(f"Found {main_results['total_sections']} relevant legal sections")
            
            # Top acts
            top_acts = sorted(main_results["by_act"].items(), key=lambda x: len(x[1]), reverse=True)[:3]
            for act, sections in top_acts:
                findings.append(f"{act}: {len(sections)} sections")
        
        if procedure_results["total_procedures"] > 0:
            findings.append(f"Found {procedure_results['total_procedures']} relevant procedures")
        
        return findings
    
    def generate_recommendations(self, query: str, main_results: Dict, procedure_results: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if main_results["total_sections"] > 0:
            recommendations.append("Review the relevant legal sections for specific provisions")
            
            # Check for criminal matters
            criminal_sections = [s for s in main_results["relevant_sections"] if 'punishment' in s.get('text', '').lower()]
            if criminal_sections:
                recommendations.append("Consider immediate legal consultation for criminal matters")
        
        if procedure_results["total_procedures"] > 0:
            recommendations.append("Follow the procedural steps outlined for your jurisdiction")
            recommendations.append("Prepare required documents as specified in procedures")
        
        if not main_results["total_sections"] and not procedure_results["total_procedures"]:
            recommendations.append("Consult with a legal professional for specialized advice")
            recommendations.append("Consider refining your query with more specific legal terms")
        
        return recommendations

def demonstrate_enhanced_analyzer():
    """Demonstrate the enhanced analyzer capabilities"""
    analyzer = EnhancedLegalQueryAnalyzer()
    
    test_queries = [
        "What is the punishment for rape in India?",
        "How to file for divorce in India?",
        "Dowry harassment case procedures and penalties"
    ]
    
    print("ENHANCED LEGAL QUERY ANALYZER")
    print("=" * 60)
    print(f"Database: 1,693+ legal sections + procedures")
    print(f"Jurisdictions: India, UK, UAE, KSA")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. QUERY: {query}")
        print("-" * 50)
        
        result = analyzer.analyze_legal_query(query)
        
        # Analysis summary
        analysis = result["analysis"]
        print(f"Type: {analysis['query_type']}")
        print(f"Domain: {analysis['legal_domain']}")
        print(f"Jurisdiction: {analysis['primary_jurisdiction']}")
        print(f"Confidence: {analysis['confidence_score']:.2f}")
        print(f"Complexity: {analysis['complexity']}")
        
        # Results summary
        sections = result["legal_sections"]
        procedures = result["procedures"]
        print(f"\nResults:")
        print(f"  Legal Sections: {sections['total_sections']}")
        print(f"  Procedures: {procedures['total_procedures']}")
        
        # Key findings
        if analysis["key_findings"]:
            print(f"\nKey Findings:")
            for finding in analysis["key_findings"]:
                print(f"  • {finding}")
        
        # Top sections
        if sections["relevant_sections"]:
            print(f"\nTop Relevant Sections:")
            for section in sections["relevant_sections"][:3]:
                print(f"  • Section {section['section_number']} ({section['act']}): {section['text'][:80]}...")
        
        # Recommendations
        if result["recommendations"]:
            print(f"\nRecommendations:")
            for rec in result["recommendations"]:
                print(f"  • {rec}")

if __name__ == "__main__":
    demonstrate_enhanced_analyzer()