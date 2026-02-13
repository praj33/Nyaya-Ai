import json
import os
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class CaseLaw:
    title: str
    court: str
    year: int
    jurisdiction: str
    domain: str
    principle: str
    keywords: List[str]

class CaseLawLoader:
    def __init__(self, data_dir: str = None, scraped_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data", "caselaw"
            )
        if scraped_dir is None:
            scraped_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data", "caselaw_scraped"
            )
        self.data_dir = data_dir
        self.scraped_dir = scraped_dir
        self.cases: List[CaseLaw] = []
    
    def load_all(self) -> List[CaseLaw]:
        """Load all case law files from data directory and scraped directory"""
        # Load existing case law
        if os.path.exists(self.data_dir):
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.data_dir, filename)
                    self._load_file(filepath)
        
        # Load scraped case law
        if os.path.exists(self.scraped_dir):
            for filename in os.listdir(self.scraped_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.scraped_dir, filename)
                    self._load_scraped_file(filepath)
        
        return self.cases
    
    def _load_file(self, filepath: str):
        """Load cases from a single JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for case_data in data:
                    case = CaseLaw(
                        title=case_data.get('title', ''),
                        court=case_data.get('court', ''),
                        year=case_data.get('year', 0),
                        jurisdiction=case_data.get('jurisdiction', 'IN'),
                        domain=case_data.get('domain', ''),
                        principle=case_data.get('principle', ''),
                        keywords=case_data.get('keywords', [])
                    )
                    self.cases.append(case)
        except Exception as e:
            print(f"Error loading case law file {filepath}: {e}")
    
    def _load_scraped_file(self, filepath: str):
        """Load scraped case from a single JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
            
            case = CaseLaw(
                title=case_data.get('title', ''),
                court=case_data.get('court', ''),
                year=case_data.get('year', 0),
                jurisdiction=case_data.get('jurisdiction', 'IN'),
                domain=case_data.get('domain', ''),
                principle=case_data.get('principle', ''),
                keywords=case_data.get('keywords', [])
            )
            self.cases.append(case)
        except Exception as e:
            print(f"Error loading scraped case law file {filepath}: {e}")
    
    def get_by_domain(self, domain: str) -> List[CaseLaw]:
        """Get all cases for a specific domain"""
        return [case for case in self.cases if case.domain == domain]
    
    def get_by_jurisdiction(self, jurisdiction: str) -> List[CaseLaw]:
        """Get all cases for a specific jurisdiction"""
        return [case for case in self.cases if case.jurisdiction == jurisdiction]
