#!/usr/bin/env python3
"""
Debug script to see what's happening in data loading
"""

import sys
import json
sys.path.append('.')

from data_bridge.loader import JSONLoader

def debug_loading():
    """Debug the loading process"""
    print("=== DEBUGGING DATA LOADING ===")
    
    loader = JSONLoader("db")
    
    # Test loading a single file
    test_file = "db/ipc_sections.json"
    print(f"Testing file: {test_file}")
    
    try:
        # Load raw JSON
        with open(test_file, 'r') as f:
            raw_data = json.load(f)
        
        print("Raw data structure:")
        print(f"Top-level keys: {list(raw_data.keys())}")
        
        if "key_sections" in raw_data:
            print(f"key_sections categories: {list(raw_data['key_sections'].keys())}")
            
            # Show first category
            first_category = list(raw_data['key_sections'].keys())[0]
            first_sections = raw_data['key_sections'][first_category]
            print(f"First category '{first_category}' has {len(first_sections)} sections")
            
            # Show first few sections
            for i, (section_num, text) in enumerate(list(first_sections.items())[:3]):
                print(f"  {section_num}: {text}")
        
        # Test the loader
        print("\n=== TESTING LOADER ===")
        sections, acts, cases = loader.load_and_normalize_file(test_file)
        print(f"Loader extracted: {len(sections)} sections, {len(acts)} acts, {len(cases)} cases")
        
        if sections:
            print("First section:")
            section = sections[0]
            print(f"  ID: {section.section_id}")
            print(f"  Number: {section.section_number}")
            print(f"  Text: {section.text}")
            print(f"  Jurisdiction: {section.jurisdiction}")
            print(f"  Act ID: {section.act_id}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_loading()