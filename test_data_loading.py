#!/usr/bin/env python3
"""
Test script to verify data loading and search functionality
"""

import sys
sys.path.append('.')

from data_bridge.loader import JSONLoader
from data_bridge.schemas.section import Jurisdiction

def test_data_loading():
    """Test if data is being loaded correctly"""
    print("=== TESTING DATA LOADING ===")
    
    loader = JSONLoader("db")
    sections, acts, cases = loader.load_and_normalize_directory()
    
    print(f"Total sections loaded: {len(sections)}")
    print(f"Total acts loaded: {len(acts)}")
    print(f"Total cases loaded: {len(cases)}")
    
    # Show sample sections
    print("\n=== SAMPLE SECTIONS ===")
    for i, section in enumerate(sections[:10]):
        print(f"{i+1}. Section {section.section_number}: {section.text[:100]}...")
        print(f"   Jurisdiction: {section.jurisdiction.value}")
        print(f"   Act ID: {section.act_id}")
        print()
    
    # Test search for theft
    print("\n=== TESTING THEFT SEARCH ===")
    theft_sections = []
    for section in sections:
        if section.jurisdiction == Jurisdiction.IN:
            if 'theft' in section.text.lower():
                theft_sections.append(section)
    
    print(f"Found {len(theft_sections)} sections containing 'theft':")
    for section in theft_sections[:5]:
        print(f"- Section {section.section_number}: {section.text}")
    
    return sections, acts, cases

if __name__ == "__main__":
    test_data_loading()