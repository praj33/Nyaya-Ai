#!/usr/bin/env python3
"""
Quick Backend Integration Test
Tests specific divorce and crime queries to verify enhanced system
"""
import requests
import json

def test_enhanced_queries():
    """Test enhanced legal advisor integration"""
    base_url = "http://localhost:8000"
    
    test_cases = [
        {
            "name": "Divorce Query (Enhanced)",
            "query": "I want divorce from my wife in India",
            "expected": ["Hindu Marriage Act", "divorce", "Section 13"]
        },
        {
            "name": "Rape Crime Query (Enhanced)", 
            "query": "What is punishment for rape in India?",
            "expected": ["Section 375", "Section 376", "rape"]
        },
        {
            "name": "Theft Query (Enhanced)",
            "query": "Theft punishment under Indian law",
            "expected": ["Section 378", "Section 379", "theft"]
        }
    ]
    
    print("Testing Enhanced Legal Advisor Integration")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"Query: {test['query']}")
        
        try:
            response = requests.post(
                f"{base_url}/nyaya/query",
                json={
                    "query": test["query"],
                    "jurisdiction_hint": "India",
                    "user_context": {"role": "citizen", "confidence_required": True}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                confidence = data.get('confidence', 0)
                sections_found = data.get('reasoning_trace', {}).get('sections_found', 0)
                
                print(f"Status: SUCCESS")
                print(f"Confidence: {confidence}")
                print(f"Sections Found: {sections_found}")
                
                # Check if response contains expected terms
                response_text = json.dumps(data).lower()
                found_terms = [term for term in test['expected'] if term.lower() in response_text]
                
                if found_terms:
                    print(f"Relevant Terms Found: {found_terms}")
                else:
                    print(f"Expected terms not found: {test['expected']}")
                    
            else:
                print(f"Status: FAILED ({response.status_code})")
                print(f"Error: {response.text[:200]}...")
                
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print(f"\n{'='*60}")
    print("Integration Test Complete!")
    print("Check results above to verify enhanced system is working")

if __name__ == "__main__":
    test_enhanced_queries()