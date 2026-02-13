#!/usr/bin/env python3
"""
Final Enhanced Test
Tests enhanced legal advisor with specific queries
"""
import requests
import json

def test_enhanced_system():
    base_url = "http://localhost:8000"
    
    # Test enhanced divorce query
    print("Testing Enhanced Legal Advisor...")
    print("=" * 50)
    
    test_query = {
        "query": "Hindu Marriage Act divorce grounds Section 13",
        "jurisdiction_hint": "India",
        "domain_hint": "civil"
    }
    
    try:
        response = requests.post(f"{base_url}/nyaya/query", json=test_query, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Enhanced system active")
            print(f"Confidence: {data.get('confidence')}")
            print(f"Sections: {data.get('reasoning_trace', {}).get('sections_found', 0)}")
            print(f"Agent: {data.get('legal_route', [])}")
            
            # Check if enhanced
            if "enhanced" in str(data.get('legal_route', [])).lower():
                print("✓ Enhanced legal advisor is active")
            else:
                print("⚠ Still using old system")
                
        else:
            print(f"FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_enhanced_system()