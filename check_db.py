#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from data_bridge.loader import JSONLoader

def check_database_sections():
    print("Checking database sections...")
    loader = JSONLoader("db")
    sections, acts, cases = loader.load_and_normalize_directory()
    
    print(f"Total sections: {len(sections)}")
    
    # Check for BNS sections
    bns_sections = [s for s in sections if 'bns' in s.act_id.lower()]
    print(f"BNS sections: {len(bns_sections)}")
    
    # Check for section 103
    section_103 = [s for s in sections if s.section_number == '103']
    print(f"Section 103 found: {len(section_103)}")
    
    if section_103:
        for s in section_103:
            print(f"  - Act: {s.act_id}, Section: {s.section_number}, Text: {s.text[:100]}...")
    
    # Check act_id formats
    act_ids = set(s.act_id for s in sections[:10])
    print(f"Sample act_ids: {act_ids}")

if __name__ == "__main__":
    check_database_sections()