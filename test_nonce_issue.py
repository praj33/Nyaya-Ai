import requests
import json
import time

def test_nonce_issue():
    """Test nonce handling specifically to isolate the issue."""
    
    print("=== Testing Nonce Handling ===\n")
    
    # Test 1: Get nonce and immediately use it (working case)
    print("Test 1: Immediate nonce usage (multi_jurisdiction)...")
    nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
    nonce = nonce_response.json()['nonce']
    print(f"  Got nonce: {nonce}")
    
    payload = {
        'query': 'Test query',
        'jurisdictions': ['India']
    }
    
    response = requests.post(
        f'http://localhost:8000/nyaya/multi_jurisdiction?nonce={nonce}',
        json=payload
    )
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  ✓ Success")
    else:
        print(f"  ✗ Failed: {response.text}")
    
    print()
    
    # Test 2: Get nonce and immediately use it (failing case)
    print("Test 2: Immediate nonce usage (query)...")
    nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
    nonce = nonce_response.json()['nonce']
    print(f"  Got nonce: {nonce}")
    
    payload = {
        'query': 'Test query',
        'user_context': {'role': 'citizen', 'confidence_required': True}
    }
    
    response = requests.post(
        f'http://localhost:8000/nyaya/query?nonce={nonce}',
        json=payload
    )
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  ✓ Success")
    elif response.status_code == 400:
        print(f"  ✗ 400 Error: {response.json()}")
    else:
        print(f"  Other error: {response.text}")
    
    print()
    
    # Test 3: Check nonce state after generation
    print("Test 3: Check nonce state...")
    nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
    nonce = nonce_response.json()['nonce']
    print(f"  Got nonce: {nonce}")
    
    state_response = requests.get('http://localhost:8000/debug/nonce-state')
    state = state_response.json()
    print(f"  Pending nonces: {state['pending_nonces_count']}")
    print(f"  Used nonces: {state['used_nonces_count']}")
    print(f"  Nonce in pending: {nonce in state['pending_nonces']}")
    
    print()
    
    # Test 4: Use the same nonce immediately
    print("Test 4: Using same nonce immediately (query)...")
    payload = {
        'query': 'Test query',
        'user_context': {'role': 'citizen', 'confidence_required': True}
    }
    
    response = requests.post(
        f'http://localhost:8000/nyaya/query?nonce={nonce}',
        json=payload
    )
    
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print("  ✓ Success")
    elif response.status_code == 400:
        error_detail = response.json()
        print(f"  ✗ 400 Error: {error_detail}")
    else:
        print(f"  Other error: {response.text}")

if __name__ == "__main__":
    test_nonce_issue()