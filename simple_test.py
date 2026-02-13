#!/usr/bin/env python3
"""
Simple Enhanced Test
"""
import requests

def simple_test():
    try:
        response = requests.post(
            "http://localhost:8000/nyaya/query",
            json={
                "query": "theft punishment India",
                "user_context": {"role": "citizen"}
            },
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS - Enhanced system working!")
            print(f"Confidence: {data.get('confidence')}")
            print(f"Sections: {data.get('reasoning_trace', {}).get('sections_found', 0)}")
            print(f"Route: {data.get('legal_route', [])}")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    simple_test()