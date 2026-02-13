#!/usr/bin/env python3
"""
Detailed Section Counter
Properly counts all sections in nested JSON structures
"""
import json
import os

def count_sections_in_file(filename, data):
    """Count sections in a single file with detailed structure analysis"""
    sections = 0
    acts = set()
    structure_info = []
    
    if isinstance(data, dict):
        if "key_sections" in data:
            # IPC structure
            for category, category_sections in data["key_sections"].items():
                if isinstance(category_sections, dict):
                    sections += len(category_sections)
                    acts.add(f"IPC_{category}")
                    structure_info.append(f"IPC {category}: {len(category_sections)} sections")
        
        elif "structure" in data:
            # BNS structure
            for category, category_sections in data["structure"].items():
                if isinstance(category_sections, dict):
                    sections += len(category_sections)
                    acts.add(f"BNS_{category}")
                    structure_info.append(f"BNS {category}: {len(category_sections)} sections")
        
        elif "sections" in data:
            # Direct sections structure
            if isinstance(data["sections"], list):
                sections = len(data["sections"])
                acts.add("direct_sections")
            elif isinstance(data["sections"], dict):
                sections = len(data["sections"])
                acts.add("sections_dict")
        
        else:
            # Check for other patterns
            for key, value in data.items():
                if isinstance(value, dict):
                    # Check if it's a section-like structure
                    if all(k.isdigit() or k.replace('.', '').replace('A', '').replace('B', '').isdigit() 
                           for k in value.keys() if isinstance(k, str)):
                        sections += len(value)
                        acts.add(key)
                        structure_info.append(f"{key}: {len(value)} sections")
                elif isinstance(value, list):
                    sections += len(value)
                    acts.add(key)
                    structure_info.append(f"{key}: {len(value)} sections")
    
    elif isinstance(data, list):
        sections = len(data)
        acts.add("list_structure")
    
    return sections, acts, structure_info

def detailed_count():
    """Perform detailed count of all sections"""
    db_path = "db"
    total_sections = 0
    total_acts = set()
    file_details = []
    
    print("DETAILED SECTION COUNTING")
    print("=" * 60)
    
    for filename in sorted(os.listdir(db_path)):
        if filename.endswith('.json'):
            filepath = os.path.join(db_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                sections, acts, structure_info = count_sections_in_file(filename, data)
                total_sections += sections
                total_acts.update(acts)
                
                file_details.append({
                    'filename': filename,
                    'sections': sections,
                    'acts': len(acts),
                    'structure_info': structure_info
                })
                
                print(f"\n{filename}:")
                print(f"  Sections: {sections}")
                print(f"  Acts/Categories: {len(acts)}")
                if structure_info:
                    for info in structure_info[:5]:  # Show first 5
                        print(f"    - {info}")
                    if len(structure_info) > 5:
                        print(f"    ... and {len(structure_info) - 5} more categories")
                
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    print(f"\n{'='*60}")
    print("FINAL TOTALS:")
    print(f"Total Files: {len(file_details)}")
    print(f"Total Sections: {total_sections:,}")
    print(f"Total Acts/Categories: {len(total_acts)}")
    
    # Top files by sections
    print(f"\nTOP FILES BY SECTIONS:")
    sorted_files = sorted(file_details, key=lambda x: x['sections'], reverse=True)
    for i, file_info in enumerate(sorted_files[:10], 1):
        print(f"  {i:2}. {file_info['filename']:<35} - {file_info['sections']:,} sections")
    
    # Files with no sections
    empty_files = [f for f in file_details if f['sections'] == 0]
    if empty_files:
        print(f"\nFILES WITH NO SECTIONS ({len(empty_files)}):")
        for file_info in empty_files:
            print(f"  - {file_info['filename']}")
    
    return total_sections, len(total_acts), file_details

if __name__ == "__main__":
    detailed_count()