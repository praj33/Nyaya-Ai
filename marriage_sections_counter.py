#!/usr/bin/env python3
"""
Marriage Sections Counter
Counts all marriage-related sections across all jurisdictions
"""
import json
import os

def count_marriage_sections():
    """Count marriage sections across all jurisdictions"""
    db_path = "db"
    marriage_sections = {
        "India": [],
        "UK": [],
        "UAE": [],
        "Total": 0
    }
    
    marriage_keywords = [
        'marriage', 'marry', 'married', 'divorce', 'matrimonial', 'spouse', 
        'husband', 'wife', 'dowry', 'wedding', 'marital', 'bigamy', 
        'polygamy', 'cohabitation', 'separation', 'custody', 'alimony',
        'maintenance', 'nikah', 'aqd', 'mahr', 'khula', 'talaq'
    ]
    
    print("MARRIAGE SECTIONS ANALYSIS")
    print("=" * 50)
    
    for filename in os.listdir(db_path):
        if filename.endswith('.json'):
            filepath = os.path.join(db_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Detect jurisdiction
                jurisdiction = "India"
                if any(x in filename.lower() for x in ['uk', 'britain']):
                    jurisdiction = "UK"
                elif any(x in filename.lower() for x in ['uae', 'emirates']):
                    jurisdiction = "UAE"
                
                # Search for marriage sections
                file_marriage_sections = find_marriage_sections_in_file(data, filename, marriage_keywords)
                
                if file_marriage_sections:
                    print(f"\n{filename} ({jurisdiction}):")
                    for section in file_marriage_sections:
                        print(f"  - Section {section['number']}: {section['text'][:80]}...")
                        marriage_sections[jurisdiction].append(section)
                        marriage_sections["Total"] += 1
                
            except Exception as e:
                continue
    
    # Summary
    print(f"\n{'='*50}")
    print("MARRIAGE SECTIONS SUMMARY")
    print(f"{'='*50}")
    
    for jurisdiction in ["India", "UK", "UAE"]:
        count = len(marriage_sections[jurisdiction])
        print(f"{jurisdiction}: {count} sections")
        
        if count > 0:
            print("  Key sections:")
            for section in marriage_sections[jurisdiction][:5]:
                print(f"    • Section {section['number']}: {section['text'][:60]}...")
            if count > 5:
                print(f"    ... and {count - 5} more sections")
    
    print(f"\nTOTAL MARRIAGE SECTIONS: {marriage_sections['Total']}")
    
    return marriage_sections

def find_marriage_sections_in_file(data, filename, keywords):
    """Find marriage-related sections in a file"""
    sections = []
    
    if isinstance(data, dict):
        # IPC structure
        if "key_sections" in data:
            for category, category_sections in data["key_sections"].items():
                if isinstance(category_sections, dict):
                    for num, text in category_sections.items():
                        if isinstance(text, str) and is_marriage_related(text, keywords):
                            sections.append({
                                "number": num,
                                "text": text,
                                "category": category,
                                "file": filename
                            })
        
        # BNS structure
        elif "structure" in data:
            for category, category_sections in data["structure"].items():
                if isinstance(category_sections, dict):
                    for num, text in category_sections.items():
                        if isinstance(text, str) and is_marriage_related(text, keywords):
                            sections.append({
                                "number": num,
                                "text": text,
                                "category": category,
                                "file": filename
                            })
        
        # Other structures
        else:
            for key, value in data.items():
                if isinstance(value, dict):
                    for section_key, section_value in value.items():
                        if isinstance(section_value, str) and is_marriage_related(section_value, keywords):
                            sections.append({
                                "number": section_key,
                                "text": section_value,
                                "category": key,
                                "file": filename
                            })
                        elif isinstance(section_value, dict):
                            # Handle nested structures like UAE law
                            if "offence" in section_value:
                                offence_text = section_value["offence"]
                                if is_marriage_related(offence_text, keywords):
                                    sections.append({
                                        "number": section_key,
                                        "text": offence_text,
                                        "category": key,
                                        "file": filename
                                    })
                            # Check for marriage-specific keys
                            elif "marriage" in section_key.lower() or "divorce" in section_key.lower():
                                sections.append({
                                    "number": section_key,
                                    "text": section_value.get("offence", str(section_value)[:100]),
                                    "category": key,
                                    "file": filename
                                })
    
    return sections

def is_marriage_related(text, keywords):
    """Check if text is marriage-related"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

if __name__ == "__main__":
    count_marriage_sections()