#!/usr/bin/env python3
"""
Script to generate a valid nonce and test the API endpoint
"""
import requests
import json
import subprocess
import time

def generate_nonce_via_api():
    """Generate a nonce by accessing the API's nonce manager"""
    # This simulates what the API would do internally
    from provenance_chain.nonce_manager import nonce_manager
    return nonce_manager.generate_nonce()

def test_api_with_generated_nonce():
    """Test the API with a properly generated nonce"""
    # Generate nonce
    nonce = generate_nonce_via_api()
    print(f"Generated nonce: {nonce}")
    
    # Test the API
    url = f'http://localhost:8000/nyaya/query?nonce={nonce}'
    payload = {
        "query": "What is the punishment for theft in India?",
        "jurisdiction_hint": "India", 
        "domain_hint": "criminal",
        "user_context": {
            "role": "citizen",
            "confidence_required": True
        }
    }
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    print(f"Making request to: {url}")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Response:")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Error Response:")
        print(json.dumps(response.json(), indent=2))
    
    return response.status_code == 200

if __name__ == "__main__":
    print("=== Testing Nyaya API with Generated Nonce ===")
    success = test_api_with_generated_nonce()
    if success:
        print("\n✅ API test successful!")
    else:
        print("\n❌ API test failed!")