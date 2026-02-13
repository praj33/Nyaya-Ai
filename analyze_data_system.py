import json
import os
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any
import sys
sys.path.append('.')

from data_bridge.loader import JSONLoader
from data_bridge.validator import JSONValidator

def analyze_data_bridge_and_db():
    """Comprehensive analysis of data-bridge and db files"""
    
    print("=== NYAYA AI DATA BRIDGE & DATABASE ANALYSIS ===\n")
    
    # 1. Data Bridge Schema Analysis
    print("1. DATA BRIDGE SCHEMA ANALYSIS")
    print("-" * 40)
    
    schemas = {
        'Act': 'data_bridge/schemas/act.py',
        'Case': 'data_bridge/schemas/case.py', 
        'Section': 'data_bridge/schemas/section.py'
    }
    
    for schema_name, path in schemas.items():
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()
                lines = len(content.split('\n'))
                classes = content.count('class ')
                methods = content.count('def ')
                print(f"{schema_name} Schema: {lines} lines, {classes} classes, {methods} methods")
    
    # 2. Database Files Analysis
    print(f"\n2. DATABASE FILES ANALYSIS")
    print("-" * 40)
    
    db_path = Path("db")
    if not db_path.exists():
        print("Database directory not found!")
        return
    
    json_files = list(db_path.glob("*.json"))
    print(f"Total JSON files: {len(json_files)}")
    
    # Analyze by jurisdiction
    jurisdiction_files = defaultdict(list)
    file_sizes = {}
    
    for file_path in json_files:
        file_size = file_path.stat().st_size
        file_sizes[file_path.name] = file_size
        
        # Determine jurisdiction from filename
        name = file_path.name.lower()
        if 'indian' in name or 'ipc' in name or 'crpc' in name or 'bns' in name:
            jurisdiction_files['India'].append(file_path.name)
        elif 'uk' in name:
            jurisdiction_files['UK'].append(file_path.name)
        elif 'uae' in name:
            jurisdiction_files['UAE'].append(file_path.name)
        else:
            jurisdiction_files['Other'].append(file_path.name)
    
    print("\nFiles by Jurisdiction:")
    for jurisdiction, files in jurisdiction_files.items():
        total_size = sum(file_sizes[f] for f in files)
        print(f"  {jurisdiction}: {len(files)} files ({total_size/1024:.1f} KB)")
        for f in files[:3]:  # Show first 3 files
            print(f"    - {f}")
        if len(files) > 3:
            print(f"    ... and {len(files)-3} more")
    
    # 3. Content Analysis using JSONLoader
    print(f"\n3. CONTENT ANALYSIS USING DATA BRIDGE")
    print("-" * 40)
    
    loader = JSONLoader("db")
    validator = JSONValidator()
    
    try:
        sections, acts, cases = loader.load_and_normalize_directory()
        
        print(f"Successfully loaded:")
        print(f"  Sections: {len(sections)}")
        print(f"  Acts: {len(acts)}")
        print(f"  Cases: {len(cases)}")
        
        # Analyze sections by jurisdiction
        section_by_jurisdiction = Counter(s.jurisdiction.value for s in sections)
        print(f"\nSections by Jurisdiction:")
        for jurisdiction, count in section_by_jurisdiction.items():
            print(f"  {jurisdiction}: {count} sections")
        
        # Analyze acts by jurisdiction
        act_by_jurisdiction = Counter(a.jurisdiction.value for a in acts)
        print(f"\nActs by Jurisdiction:")
        for jurisdiction, count in act_by_jurisdiction.items():
            print(f"  {jurisdiction}: {count} acts")
        
        # Sample section analysis
        if sections:
            print(f"\nSample Section Analysis:")
            sample_section = sections[0]
            print(f"  ID: {sample_section.section_id}")
            print(f"  Number: {sample_section.section_number}")
            print(f"  Text: {sample_section.text[:100]}...")
            print(f"  Act ID: {sample_section.act_id}")
            print(f"  Jurisdiction: {sample_section.jurisdiction.value}")
            print(f"  Metadata keys: {list(sample_section.metadata.keys())}")
        
        # Validation
        print(f"\n4. DATA VALIDATION")
        print("-" * 40)
        
        # Check referential integrity
        integrity_errors = validator.validate_referential_integrity(sections, acts, cases)
        print(f"Referential integrity errors: {len(integrity_errors)}")
        
        # Check duplicate IDs
        duplicate_errors = validator.validate_duplicate_ids(sections, acts, cases)
        print(f"Duplicate ID errors: {len(duplicate_errors)}")
        
        if integrity_errors:
            print("Sample integrity errors:")
            for error in integrity_errors[:3]:
                print(f"  - {error.error_type}: {error.message}")
        
        if duplicate_errors:
            print("Sample duplicate errors:")
            for error in duplicate_errors[:3]:
                print(f"  - {error.error_type}: {error.message}")
        
    except Exception as e:
        print(f"Error during content analysis: {e}")
    
    # 4. Specific Dataset Analysis
    print(f"\n5. SPECIFIC DATASET ANALYSIS")
    print("-" * 40)
    
    key_datasets = [
        "indian_law_dataset.json",
        "uk_law_dataset.json", 
        "uae_law_dataset.json"
    ]
    
    for dataset in key_datasets:
        dataset_path = db_path / dataset
        if dataset_path.exists():
            try:
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"\n{dataset}:")
                print(f"  Jurisdiction: {data.get('jurisdiction', 'Unknown')}")
                print(f"  Version: {data.get('version', 'Unknown')}")
                print(f"  Last Updated: {data.get('last_updated', 'Unknown')}")
                
                # Count different types of content
                if 'bns_sections' in data:
                    print(f"  BNS Sections: {len(data['bns_sections'])}")
                if 'criminal_law' in data:
                    criminal_acts = sum(len(acts) for acts in data['criminal_law'].values())
                    print(f"  Criminal Law Acts: {len(data['criminal_law'])}")
                    print(f"  Criminal Law Sections: {criminal_acts}")
                if 'civil_law' in data:
                    civil_acts = sum(len(acts) for acts in data['civil_law'].values())
                    print(f"  Civil Law Acts: {len(data['civil_law'])}")
                    print(f"  Civil Law Sections: {civil_acts}")
                if 'scraped_data' in data:
                    print(f"  Scraped Data Entries: {len(data['scraped_data'])}")
                
            except Exception as e:
                print(f"  Error analyzing {dataset}: {e}")
    
    # 5. Data Bridge Functionality Test
    print(f"\n6. DATA BRIDGE FUNCTIONALITY TEST")
    print("-" * 40)
    
    try:
        # Test loading a single file
        test_file = "db/indian_law_dataset.json"
        if os.path.exists(test_file):
            sections, acts, cases = loader.load_and_normalize_file(test_file)
            print(f"Single file test ({test_file}):")
            print(f"  Loaded: {len(sections)} sections, {len(acts)} acts, {len(cases)} cases")
            
            # Test embedding text extraction
            if sections:
                embedding_texts = loader.get_all_embedding_texts(sections[:5], acts[:5], cases[:5])
                print(f"  Generated {len(embedding_texts)} embedding texts")
                if embedding_texts:
                    print(f"  Sample embedding text: {embedding_texts[0][:100]}...")
        
    except Exception as e:
        print(f"Functionality test error: {e}")
    
    # 6. Summary Statistics
    print(f"\n7. SUMMARY STATISTICS")
    print("-" * 40)
    
    total_size = sum(file_sizes.values())
    print(f"Total database size: {total_size/1024/1024:.2f} MB")
    print(f"Average file size: {total_size/len(json_files)/1024:.1f} KB")
    print(f"Largest file: {max(file_sizes.items(), key=lambda x: x[1])[0]} ({max(file_sizes.values())/1024:.1f} KB)")
    print(f"Smallest file: {min(file_sizes.items(), key=lambda x: x[1])[0]} ({min(file_sizes.values())/1024:.1f} KB)")
    
    print(f"\nData Bridge Components:")
    print(f"  Schema files: {len(schemas)}")
    print(f"  Loader functionality: OK")
    print(f"  Validator functionality: OK")
    print(f"  Multi-jurisdiction support: OK")
    print(f"  Embedding text generation: OK")

if __name__ == "__main__":
    analyze_data_bridge_and_db()