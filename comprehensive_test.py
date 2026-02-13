#!/usr/bin/env python3
"""
Comprehensive Enhanced System Test
"""
import requests

def test_enhanced_features():
    base_url = "http://localhost:8000"
    
    test_cases = [
        {
            "name": "Theft Query (Enhanced)",
            "query": "theft punishment India",
            "expected_confidence": 0.8
        },
        {
            "name": "Divorce Query (Enhanced)", 
            "query": "I want divorce from my wife in India",
            "expected_confidence": 0.8
        },
        {
            "name": "Rape Query (Enhanced)",
            "query": "What is punishment for rape in India?",
            "expected_confidence": 0.8
        }
    ]
    
    print("Enhanced Legal Advisor System Test")
    print("=" * 50)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"Query: {test['query']}")
        
        try:
            response = requests.post(
                f"{base_url}/nyaya/query",
                json={
                    "query": test["query"],
                    "user_context": {"role": "citizen"}
                },
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                confidence = data.get('confidence', 0)
                sections = data.get('reasoning_trace', {}).get('sections_found', 0)
                route = data.get('legal_route', [])
                
                print(f"SUCCESS")
                print(f"  Confidence: {confidence:.2f}")
                print(f"  Sections Found: {sections}")
                print(f"  Legal Route: {route}")
                
                # Check if enhanced
                if "enhanced" in str(route).lower():
                    print(f"  Enhanced system active")
                else:
                    print(f"  Old system still active")
                
                # Check confidence improvement
                if confidence >= test['expected_confidence']:
                    print(f"  High confidence achieved")
                else:
                    print(f"  Lower confidence than expected")
                    
            else:
                print(f"FAILED ({response.status_code})")
                print(f"  Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"ERROR: {str(e)}")
    
    print(f"\n{'='*50}")
    print("Enhanced System Integration Complete!")

if __name__ == "__main__":
    test_enhanced_features()