#!/usr/bin/env python3
"""
Test script that generates nonce through the API server and uses it for requests
"""
import requests
import json
import time

def test_api_with_server_generated_nonce():
    """Test the API by getting a nonce from the server and using it"""
    
    # Step 1: Get a valid nonce from the server
    print("=== Step 1: Getting nonce from server ===")
    nonce_response = requests.get("http://localhost:8000/debug/generate-nonce")
    
    if nonce_response.status_code != 200:
        print(f"Failed to get nonce: {nonce_response.status_code}")
        print(nonce_response.text)
        return False
    
    nonce_data = nonce_response.json()
    nonce = nonce_data["nonce"]
    print(f"Generated nonce: {nonce}")
    print(f"Expires in: {nonce_data['expires_in_seconds']} seconds")
    
    # Step 2: Use the nonce to make a query
    print("\n=== Step 2: Making API request with nonce ===")
    url = f"http://localhost:8000/nyaya/query?nonce={nonce}"
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
        print("✅ Success! Response:")
        print(json.dumps(response.json(), indent=2))
        return True
    else:
        print("❌ Error Response:")
        print(json.dumps(response.json(), indent=2))
        return False

def test_nonce_reuse_protection():
    """Test that the same nonce cannot be used twice"""
    print("\n=== Testing nonce reuse protection ===")
    
    # Get a nonce
    nonce_response = requests.get("http://localhost:8000/debug/generate-nonce")
    nonce = nonce_response.json()["nonce"]
    print(f"Generated nonce: {nonce}")
    
    # Use it once (should succeed)
    url = f"http://localhost:8000/nyaya/query?nonce={nonce}"
    payload = {
        "query": "Test query 1",
        "jurisdiction_hint": "India",
        "domain_hint": "criminal"
    }
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    
    print("First use (should succeed)...")
    response1 = requests.post(url, json=payload, headers=headers)
    print(f"First request status: {response1.status_code}")
    
    # Use it again (should fail)
    print("Second use (should fail)...")
    response2 = requests.post(url, json=payload, headers=headers)
    print(f"Second request status: {response2.status_code}")
    
    if response1.status_code == 200 and response2.status_code == 400:
        print("✅ Nonce reuse protection working correctly")
        return True
    else:
        print("❌ Nonce reuse protection not working")
        return False

if __name__ == "__main__":
    print("=== Testing Nyaya API with Server-Generated Nonce ===")
    
    success1 = test_api_with_server_generated_nonce()
    success2 = test_nonce_reuse_protection()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Nonce system is working correctly.")
    else:
        print("\n❌ Some tests failed!")