"""
JSON dataset loader and normalizer for legal datasets
"""
import json
import os
from typing import Dict, Any, List, Tuple, Optional, Union
from pathlib import Path
import logging
from .schemas.section import Section, Jurisdiction
from .schemas.act import Act
from .schemas.case import Case
from .validator import JSONValidator


class JSONLoader:
    """
    JSON-specific loader that:
    - Loads JSON files safely (streaming where possible)
    - Detects dataset type (section / act / case)
    - Maps non-standard keys to standard schema
    - Assigns jurisdiction explicitly (fallback defaults allowed)
    - Preserves original JSON fields inside metadata
    - Produces clean, normalized Python dictionaries
    - Supports bulk loading and single-file loading
    - Is idempotent and deterministic
    """
    
    def __init__(self, input_directory: Optional[str] = None):
        self.input_directory = input_directory or "db"
        self.validator = JSONValidator()
        self.logger = logging.getLogger(__name__)
        
    def load_json_file(self, file_path: str) -> Dict[str, Any]:
        """Safely load a JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in file {file_path}: {e}")
            raise
        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading file {file_path}: {e}")
            raise
    
    def detect_jurisdiction_from_path(self, file_path: str) -> Jurisdiction:
        """Detect jurisdiction based on file path"""
        path_lower = file_path.lower()
        
        if 'indian' in path_lower or 'ipc' in path_lower or 'crpc' in path_lower or \
           'cpc' in path_lower or 'bns' in path_lower or 'in' in path_lower:
            return Jurisdiction.IN
        elif 'uk' in path_lower:
            return Jurisdiction.UK
        elif 'uae' in path_lower:
            return Jurisdiction.UAE
        else:
            # Default to India if no clear indicator
            return Jurisdiction.IN
    
    def normalize_section(self, section_data: Dict[str, Any], jurisdiction: Jurisdiction, 
                         original_key: str = None, act_id: str = None) -> Section:
        """Normalize a section object to the standard schema"""
        # Extract data with flexible key mapping
        section_id = section_data.get("section_id", 
                                    section_data.get("section", 
                                                   section_data.get("id", 
                                                                  section_data.get("section_number", original_key or ""))))
        
        # Ensure section_id is unique by including the act_id
        if act_id and section_id:
            section_id = f"{act_id}_{section_id}"
        elif act_id and original_key:
            section_id = f"{act_id}_{original_key}"
        elif not section_id:
            section_id = f"{act_id}_{original_key}" if act_id and original_key else original_key or "unknown"
        
        section_number = section_data.get("section_number", 
                                        section_data.get("section", 
                                                       section_data.get("id", 
                                                                      section_data.get("number", original_key or ""))))
        
        text = section_data.get("text", 
                              section_data.get("content", 
                                             section_data.get("description", 
                                                            section_data.get("offence", 
                                                                           section_data.get("title", "")))))
        
        # Use provided act_id or try to extract from data
        resolved_act_id = act_id or section_data.get("act_id", 
                                                   section_data.get("act", 
                                                                  f"{jurisdiction.value}_act_unknown"))
        
        # Preserve original data in metadata
        metadata = section_data.copy()
        # Remove fields that are already part of the standard schema
        for key in ["section_id", "section_number", "text", "act_id", "act", "content", 
                   "description", "offence", "title", "id", "number"]:
            metadata.pop(key, None)
        
        return Section(
            section_id=str(section_id),
            section_number=str(section_number),
            text=str(text),
            act_id=resolved_act_id,
            jurisdiction=jurisdiction,
            metadata=metadata
        )
    
    def normalize_act(self, act_data: Dict[str, Any], jurisdiction: Jurisdiction, 
                     act_id: str = None) -> Act:
        """Normalize an act object to the standard schema"""
        # Extract data with flexible key mapping
        resolved_act_id = act_id or act_data.get("act_id", 
                                               act_data.get("id", 
                                                          act_data.get("act_name", 
                                                                     f"{jurisdiction.value}_act_unknown")))
        
        act_name = act_data.get("act_name", 
                              act_data.get("title", 
                                         act_data.get("name", 
                                                    act_data.get("description", ""))))
        
        year = act_data.get("year", 
                          act_data.get("enactment_year", 
                                     act_data.get("date", 0)))
        
        if isinstance(year, str) and year.isdigit():
            year = int(year)
        elif not isinstance(year, int):
            year = 0
        
        sections = act_data.get("sections", 
                              act_data.get("section_list", []))
        
        # Ensure sections is a list of strings
        if isinstance(sections, list):
            sections = [str(s) for s in sections]
        else:
            sections = []
        
        # Preserve original data in metadata
        metadata = act_data.copy()
        # Remove fields that are already part of the standard schema
        for key in ["act_id", "id", "act_name", "title", "name", "description", 
                   "year", "enactment_year", "date", "sections", "section_list"]:
            metadata.pop(key, None)
        
        return Act(
            act_id=str(resolved_act_id),
            act_name=str(act_name),
            year=year,
            jurisdiction=jurisdiction,
            sections=sections,
            metadata=metadata
        )
    
    def normalize_case(self, case_data: Dict[str, Any], jurisdiction: Jurisdiction, 
                      case_id: str = None) -> Case:
        """Normalize a case object to the standard schema"""
        # Extract data with flexible key mapping
        resolved_case_id = case_id or case_data.get("case_id", 
                                                  case_data.get("id", 
                                                              case_data.get("title", 
                                                                          f"{jurisdiction.value}_case_unknown")))
        
        title = case_data.get("title", 
                            case_data.get("name", 
                                        case_data.get("case_title", 
                                                    case_data.get("case_name", ""))))
        
        court = case_data.get("court", 
                            case_data.get("court_name", 
                                        case_data.get("tribunal", "")))
        
        citations = case_data.get("citations", 
                                case_data.get("citation", 
                                            case_data.get("references", [])))
        
        if not isinstance(citations, list):
            citations = [str(citations)] if citations else []
        
        summary = case_data.get("summary", 
                              case_data.get("description", 
                                          case_data.get("content", 
                                                      case_data.get("judgment", ""))))
        
        referenced_sections = case_data.get("referenced_sections", 
                                          case_data.get("sections", 
                                                      case_data.get("section_list", [])))
        
        if not isinstance(referenced_sections, list):
            referenced_sections = [str(rs) for rs in referenced_sections] if referenced_sections else []
        
        # Preserve original data in metadata
        metadata = case_data.copy()
        # Remove fields that are already part of the standard schema
        for key in ["case_id", "id", "title", "name", "case_title", "case_name", 
                   "court", "court_name", "tribunal", "citations", "citation", 
                   "references", "summary", "description", "content", "judgment", 
                   "referenced_sections", "sections", "section_list"]:
            metadata.pop(key, None)
        
        return Case(
            case_id=str(resolved_case_id),
            title=str(title),
            court=str(court),
            jurisdiction=jurisdiction,
            citations=citations,
            summary=str(summary),
            referenced_sections=referenced_sections,
            metadata=metadata
        )
    
    def extract_sections_from_dataset(self, data: Dict[str, Any], 
                                    jurisdiction: Jurisdiction, 
                                    file_path: str = "") -> List[Section]:
        """Extract sections from various dataset structures"""
        sections = []
        
        # Handle different JSON structures
        if "key_sections" in data:
            # IPC-style structure: {"key_sections": {"category": {"section_num": "text"}}}
            # Extract act_id from file path
            file_name = os.path.basename(file_path).replace('.json', '')
            act_id = f"{jurisdiction.value}_{file_name}"
            
            for category, sections_dict in data["key_sections"].items():
                for section_num, text in sections_dict.items():
                    section_obj = self.normalize_section(
                        {
                            "section_number": section_num,
                            "text": text,
                            "category": category
                        },
                        jurisdiction,
                        original_key=section_num,
                        act_id=act_id
                    )
                    sections.append(section_obj)
        elif "bns_sections" in data:
            # BNS-style structure: {"bns_sections": {"offence_name": {...}}}
            # Extract act_id from file path
            file_name = os.path.basename(file_path).replace('.json', '')
            act_id = f"{jurisdiction.value}_{file_name}"
            
            for offence_name, offence_data in data["bns_sections"].items():
                if isinstance(offence_data, dict):
                    section_obj = self.normalize_section(
                        {
                            "section_number": offence_name,
                            "text": offence_data.get("offence", ""),
                            "elements_required": offence_data.get("elements_required", []),
                            "punishment": offence_data.get("punishment", ""),
                            "process_steps": offence_data.get("process_steps", [])
                        },
                        jurisdiction,
                        original_key=offence_name,
                        act_id=act_id
                    )
                    sections.append(section_obj)
        elif "structure" in data:
            # BNS/UK Criminal Justice Act structure
            file_name = os.path.basename(file_path).replace('.json', '')
            act_id = f"{jurisdiction.value}_{file_name}"
            
            for category, sections_dict in data["structure"].items():
                if isinstance(sections_dict, dict):
                    for section_num, section_text in sections_dict.items():
                        if isinstance(section_text, str) and not section_num.lower().startswith('title'):
                            section_obj = self.normalize_section(
                                {
                                    "section_number": section_num,
                                    "text": section_text,
                                    "category": category
                                },
                                jurisdiction,
                                original_key=section_num,
                                act_id=act_id
                            )
                            sections.append(section_obj)
        elif "key_provisions" in data:
            # Hindu Marriage Act style: {"key_provisions": {"category": {"Section_X": "text"}}}
            file_name = os.path.basename(file_path).replace('.json', '')
            act_id = f"{jurisdiction.value}_{file_name}"
            
            if isinstance(data["key_provisions"], dict):
                for category, provisions in data["key_provisions"].items():
                    if isinstance(provisions, dict):
                        for section_key, section_content in provisions.items():
                            # Handle both string and list content
                            if isinstance(section_content, list):
                                text = "; ".join(section_content)
                            else:
                                text = str(section_content)
                            
                            section_obj = self.normalize_section(
                                {
                                    "section_number": section_key.replace("Section_", ""),
                                    "text": text,
                                    "category": category
                                },
                                jurisdiction,
                                original_key=section_key,
                                act_id=act_id
                            )
                            sections.append(section_obj)
            elif isinstance(data["key_provisions"], list):
                for idx, provision in enumerate(data["key_provisions"]):
                    section_obj = self.normalize_section(
                        {
                            "section_number": str(idx + 1),
                            "text": str(provision),
                            "category": "key_provisions"
                        },
                        jurisdiction,
                        original_key=str(idx),
                        act_id=act_id
                    )
                    sections.append(section_obj)
        elif "sections" in data:
            # Direct sections array or object
            # Extract act_id from file path
            file_name = os.path.basename(file_path).replace('.json', '')
            act_id = f"{jurisdiction.value}_{file_name}"
            
            if isinstance(data["sections"], list):
                for idx, section_data in enumerate(data["sections"]):
                    if isinstance(section_data, dict):
                        section_obj = self.normalize_section(
                            section_data,
                            jurisdiction,
                            original_key=str(idx),
                            act_id=act_id
                        )
                        sections.append(section_obj)
            elif isinstance(data["sections"], dict):
                for section_key, section_data in data["sections"].items():
                    if isinstance(section_data, dict):
                        section_obj = self.normalize_section(
                            section_data,
                            jurisdiction,
                            original_key=section_key,
                            act_id=act_id
                        )
                        sections.append(section_obj)
                    else:
                        # If the value is just text, create a basic section
                        section_obj = self.normalize_section(
                            {
                                "section_number": section_key,
                                "text": str(section_data)
                            },
                            jurisdiction,
                            original_key=section_key,
                            act_id=act_id
                        )
                        sections.append(section_obj)
        elif "bns_sections" in data and "jurisdiction" in data:
            # Special handling for datasets like indian_law_dataset.json
            file_name = os.path.basename(file_path).replace('.json', '')
            act_id = f"{jurisdiction.value}_{file_name}"
            
            for section_name, section_data in data["bns_sections"].items():
                if isinstance(section_data, dict):
                    section_obj = self.normalize_section(
                        {
                            "section_number": section_data.get("section", section_name),
                            "text": section_data.get("offence", ""),
                            "elements_required": section_data.get("elements_required", []),
                            "punishment": section_data.get("punishment", ""),
                            "process_steps": section_data.get("process_steps", [])
                        },
                        jurisdiction,
                        original_key=section_name,
                        act_id=act_id
                    )
                    sections.append(section_obj)
        elif "criminal_law" in data or "civil_law" in data:
            # Handle UK law datasets with nested structure
            for law_type, law_content in data.items():
                if law_type in ["criminal_law", "civil_law"] and isinstance(law_content, dict):
                    for act_name, act_sections in law_content.items():
                        if isinstance(act_sections, dict):
                            for section_name, section_data in act_sections.items():
                                if isinstance(section_data, dict):
                                    section_obj = self.normalize_section(
                                        {
                                            "section_number": section_data.get("section", section_name),
                                            "text": section_data.get("offence", section_data.get("title", "")),
                                            "elements_required": section_data.get("elements_required", []),
                                            "punishment": section_data.get("punishment", ""),
                                            "process_steps": section_data.get("process_steps", []),
                                            "civil_remedies": section_data.get("civil_remedies", [])
                                        },
                                        jurisdiction,
                                        original_key=section_name,
                                        act_id=f"{jurisdiction.value}_{act_name}"
                                    )
                                    sections.append(section_obj)
        else:
            # Try to find any section-like data in the JSON
            file_name = os.path.basename(file_path).replace('.json', '')
            act_id = f"{jurisdiction.value}_{file_name}"
            
            for key, value in data.items():
                if isinstance(value, dict):
                    # Look for section-like patterns in nested objects
                    if any(section_indicator in key.lower() for section_indicator in 
                          ["section", "s.", "sec", "art", "article"]):
                        section_obj = self.normalize_section(
                            value,
                            jurisdiction,
                            original_key=key,
                            act_id=act_id
                        )
                        sections.append(section_obj)
        
        return sections
    
    def extract_acts_from_dataset(self, data: Dict[str, Any], 
                                jurisdiction: Jurisdiction, 
                                file_path: str = "") -> List[Act]:
        """Extract acts from various dataset structures"""
        acts = []
        
        # Handle different JSON structures
        if "jurisdiction" in data and "bns_sections" in data:
            # BNS-style structure with jurisdiction info (like indian_law_dataset.json)
            file_name = os.path.basename(file_path).replace('.json', '')
            act_id = f"{jurisdiction.value}_{file_name}"
            
            # Extract sections that belong to this act
            sections = []
            if "bns_sections" in data:
                for section_key in data["bns_sections"].keys():
                    sections.append(f"{act_id}_{section_key}")
            
            # Use the file name to determine act name
            clean_name = file_name.replace('_', ' ').title()
            act_name = clean_name + " Act" if not clean_name.endswith('Act') else clean_name
            version = data.get("version", "Unknown")
            
            act_obj = self.normalize_act(
                {
                    "act_id": act_id,
                    "act_name": act_name,
                    "year": self.extract_year_from_name(file_name),
                    "sections": sections
                },
                jurisdiction,
                act_id=act_id
            )
            acts.append(act_obj)
        elif "criminal_law" in data or "civil_law" in data:
            # UK-style structure: {"jurisdiction": "UK", "criminal_law": {...}}
            jurisdiction_from_data = data.get("jurisdiction", "UK")
            juris_enum = Jurisdiction(jurisdiction_from_data)
            
            # Process criminal law acts
            if "criminal_law" in data:
                for act_name, act_content in data["criminal_law"].items():
                    if isinstance(act_content, dict):
                        # Extract sections for this act
                        sections = []
                        for section_name in act_content.keys():
                            if isinstance(act_content[section_name], dict):
                                sections.append(f"{jurisdiction_from_data.lower()}_{act_name}_{section_name}")
                        
                        act_obj = self.normalize_act(
                            {
                                "act_id": f"{jurisdiction_from_data.lower()}_{act_name}",
                                "act_name": act_name.replace('_', ' ').replace('act', 'Act').title(),
                                "year": self.extract_year_from_name(act_name),  # Extract from act name if possible
                                "sections": sections
                            },
                            juris_enum
                        )
                        acts.append(act_obj)
            
            # Process civil law acts
            if "civil_law" in data:
                for act_name, act_content in data["civil_law"].items():
                    if isinstance(act_content, dict):
                        # Extract sections for this act
                        sections = []
                        for section_name in act_content.keys():
                            if isinstance(act_content[section_name], dict):
                                sections.append(f"{jurisdiction_from_data.lower()}_{act_name}_{section_name}")
                        
                        act_obj = self.normalize_act(
                            {
                                "act_id": f"{jurisdiction_from_data.lower()}_{act_name}",
                                "act_name": act_name.replace('_', ' ').replace('act', 'Act').title(),
                                "year": self.extract_year_from_name(act_name),  # Extract from act name if possible
                                "sections": sections
                            },
                            juris_enum
                        )
                        acts.append(act_obj)
        else:
            # Default act extraction based on file name or structure
            file_name = os.path.basename(file_path).replace('.json', '')
            act_id = f"{jurisdiction.value}_{file_name}"
            
            # Try to extract sections from this dataset to link to the act
            sections = []
            if "sections" in data:
                if isinstance(data["sections"], dict):
                    sections = list(data["sections"].keys())
                elif isinstance(data["sections"], list):
                    sections = [str(s) for s in data["sections"]]
            
            # For IPC-style data, extract act information
            if "key_sections" in data:
                # Use the file name to determine act name
                clean_name = file_name.replace('_sections', '').replace('_', ' ').title()
                act_name = clean_name + " Act" if not clean_name.endswith('Act') else clean_name
                
                # Extract year from file name if present
                year = self.extract_year_from_name(file_name)
                
                # Extract section IDs for this act
                section_ids = []
                if isinstance(data.get("key_sections"), dict):
                    for category, sections_dict in data["key_sections"].items():
                        for section_num in sections_dict.keys():
                            section_ids.append(f"{act_id}_{section_num}")
            
                act_obj = self.normalize_act(
                    {
                        "act_id": act_id,
                        "act_name": act_name,
                        "year": year,
                        "sections": section_ids
                    },
                    jurisdiction,
                    act_id=act_id
                )
                acts.append(act_obj)
            elif "key_provisions" in data:
                # Hindu Marriage Act style
                act_name = data.get("code", file_name.replace('_', ' ').title())
                year = self.extract_year_from_name(act_name)
                
                # Extract section IDs for this act
                section_ids = []
                if isinstance(data.get("key_provisions"), dict):
                    for category, provisions in data["key_provisions"].items():
                        if isinstance(provisions, dict):
                            for section_key in provisions.keys():
                                section_ids.append(f"{act_id}_{section_key}")
            
                act_obj = self.normalize_act(
                    {
                        "act_id": act_id,
                        "act_name": act_name,
                        "year": year,
                        "sections": section_ids
                    },
                    jurisdiction,
                    act_id=act_id
                )
                acts.append(act_obj)
            elif "bns_sections" in data and "jurisdiction" in data:
                # Handle indian_law_dataset.json style
                clean_name = file_name.replace('_', ' ').title()
                act_name = clean_name + " Act" if not clean_name.endswith('Act') else clean_name
                
                # Extract section IDs for this act
                section_ids = []
                if isinstance(data.get("bns_sections"), dict):
                    for section_name in data["bns_sections"].keys():
                        section_ids.append(f"{act_id}_{section_name}")
            
                act_obj = self.normalize_act(
                    {
                        "act_id": act_id,
                        "act_name": act_name,
                        "year": self.extract_year_from_name(file_name),
                        "sections": section_ids
                    },
                    jurisdiction,
                    act_id=act_id
                )
                acts.append(act_obj)
            elif "criminal_law" in data or "civil_law" in data:
                # Handle UK law datasets
                jurisdiction_from_data = data.get("jurisdiction", "UK")
                juris_enum = Jurisdiction(jurisdiction_from_data)
                
                # Process criminal law acts
                if "criminal_law" in data:
                    for act_name, act_content in data["criminal_law"].items():
                        if isinstance(act_content, dict):
                            # Extract sections for this act
                            sections = []
                            for section_name in act_content.keys():
                                if isinstance(act_content[section_name], dict):
                                    sections.append(f"{jurisdiction_from_data.lower()}_{act_name}_{section_name}")
                            
                            clean_act_name = act_name.replace('_', ' ').replace('act', 'Act').title()
                            act_obj = self.normalize_act(
                                {
                                    "act_id": f"{jurisdiction_from_data.lower()}_{act_name}",
                                    "act_name": clean_act_name,
                                    "year": self.extract_year_from_name(act_name),
                                    "sections": sections
                                },
                                juris_enum
                            )
                            acts.append(act_obj)
                
                # Process civil law acts
                if "civil_law" in data:
                    for act_name, act_content in data["civil_law"].items():
                        if isinstance(act_content, dict):
                            # Extract sections for this act
                            sections = []
                            for section_name in act_content.keys():
                                if isinstance(act_content[section_name], dict):
                                    sections.append(f"{jurisdiction_from_data.lower()}_{act_name}_{section_name}")
                            
                            clean_act_name = act_name.replace('_', ' ').replace('act', 'Act').title()
                            act_obj = self.normalize_act(
                                {
                                    "act_id": f"{jurisdiction_from_data.lower()}_{act_name}",
                                    "act_name": clean_act_name,
                                    "year": self.extract_year_from_name(act_name),
                                    "sections": sections
                                },
                                juris_enum
                            )
                            acts.append(act_obj)
            else:
                act_obj = self.normalize_act(
                    {
                        "act_id": act_id,
                        "act_name": file_name.replace('_', ' ').title(),
                        "year": self.extract_year_from_name(file_name),
                        "sections": sections
                    },
                    jurisdiction,
                    act_id=act_id
                )
                acts.append(act_obj)
        
        return acts
    
    def extract_cases_from_dataset(self, data: Dict[str, Any], 
                                 jurisdiction: Jurisdiction, 
                                 file_path: str = "") -> List[Case]:
        """Extract cases from various dataset structures"""
        cases = []
        
        # Currently, the existing JSON files don't contain case data
        # This method is prepared for future case datasets
        if "cases" in data:
            if isinstance(data["cases"], list):
                for case_data in data["cases"]:
                    if isinstance(case_data, dict):
                        case_obj = self.normalize_case(case_data, jurisdiction)
                        cases.append(case_obj)
            elif isinstance(data["cases"], dict):
                for case_id, case_data in data["cases"].items():
                    if isinstance(case_data, dict):
                        case_obj = self.normalize_case(case_data, jurisdiction, case_id=case_id)
                        cases.append(case_obj)
        
        return cases
    
    def load_and_normalize_file(self, file_path: str) -> Tuple[List[Section], List[Act], List[Case]]:
        """Load and normalize a single JSON file to standard schemas"""
        self.logger.info(f"Loading and normalizing file: {file_path}")
        
        # Load the JSON file
        data = self.load_json_file(file_path)
        
        # Detect jurisdiction
        jurisdiction = self.detect_jurisdiction_from_path(file_path)
        
        # Extract different types of objects
        sections = self.extract_sections_from_dataset(data, jurisdiction, file_path)
        
        # For proper linking, we need to update the acts after sections are extracted
        acts = self.extract_acts_from_dataset(data, jurisdiction, file_path)
        
        # Update act sections to match the actual sections extracted from this file
        file_name = os.path.basename(file_path).replace('.json', '')
        file_act_id = f"{jurisdiction.value}_{file_name}"
        
        # Find the act that corresponds to this file and update its sections
        for act in acts:
            if act.act_id == file_act_id:  # Update sections for the matching act regardless of current state
                # Get all sections from this file that belong to this act
                act_sections = [sec.section_id for sec in sections if sec.act_id == file_act_id]
                act.sections = act_sections
        
        cases = self.extract_cases_from_dataset(data, jurisdiction, file_path)
        
        return sections, acts, cases
    
    def load_and_normalize_directory(self, directory_path: Optional[str] = None) -> Tuple[List[Section], List[Act], List[Case]]:
        """Load and normalize all JSON files in a directory"""
        directory = directory_path or self.input_directory
        all_sections = []
        all_acts = []
        all_cases = []
        
        self.logger.info(f"Loading and normalizing directory: {directory}")
        
        # Find all JSON files in the directory
        json_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        # Process each JSON file
        for file_path in json_files:
            try:
                sections, acts, cases = self.load_and_normalize_file(file_path)
                all_sections.extend(sections)
                all_acts.extend(acts)
                all_cases.extend(cases)
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {e}")
                continue
        
        return all_sections, all_acts, all_cases
    
    def get_embedding_ready_text(self, obj: Union[Section, Act, Case]) -> str:
        """Extract clean text fields from normalized objects for embedding"""
        if isinstance(obj, Section):
            text_parts = [obj.text]
            if obj.section_number:
                text_parts.insert(0, f"Section {obj.section_number}")
            return " ".join(text_parts)
        elif isinstance(obj, Act):
            text_parts = [obj.act_name]
            if obj.act_id:
                text_parts.insert(0, f"Act: {obj.act_id}")
            return " ".join(text_parts)
        elif isinstance(obj, Case):
            text_parts = [obj.title, obj.summary]
            if obj.court:
                text_parts.insert(0, f"Case: {obj.court}")
            return " ".join([part for part in text_parts if part])
        else:
            return str(obj)
    
    def get_all_embedding_texts(self, sections: List[Section], acts: List[Act], cases: List[Case]) -> List[str]:
        """Get all embedding-ready texts from normalized objects"""
        texts = []
        
        for section in sections:
            text = self.get_embedding_ready_text(section)
            if text.strip():
                texts.append(text)
        
        for act in acts:
            text = self.get_embedding_ready_text(act)
            if text.strip():
                texts.append(text)
        
        for case in cases:
            text = self.get_embedding_ready_text(case)
            if text.strip():
                texts.append(text)
        
        return texts
    
    def extract_year_from_name(self, name: str) -> int:
        """Extract year from name string (e.g., companies_act_2013 -> 2013)"""
        import re
        # Look for 4-digit year pattern
        year_match = re.search(r'\b(19|20)\d{2}\b', name)
        if year_match:
            return int(year_match.group(0))
        return 0
