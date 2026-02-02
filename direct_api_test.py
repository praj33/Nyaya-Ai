import requests
import json
from provenance_chain.nonce_manager import nonce_manager

def test_direct_api_call():
    """Test API call with server-side nonce generation"""
    # Generate nonce in the same context as the server would
    nonce = nonce_manager.generate_nonce()
    print(f"Generated nonce: {nonce}")
    
    # Verify it's valid locally first
    local_validation = nonce_manager.validate_nonce(nonce)
    print(f"Local validation: {local_validation}")
    
    # Make API call
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
        return True
    else:
        print("Error Response:")
        print(json.dumps(response.json(), indent=2))
        return False

if __name__ == "__main__":
    print("=== Direct API Test ===")
    success = test_direct_api_call()
    if success:
        print("\n✅ Direct API test successful!")
    else:
        print("\n❌ Direct API test failed!")