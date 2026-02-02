import requests
import json

def reproduce_422_error():
    print("=== Reproducing 422 Validation Error ===")
    
    # Get a fresh nonce
    nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
    nonce = nonce_response.json()['nonce']
    print(f"Using nonce: {nonce}")
    
    # Test different payloads that might cause 422 errors
    test_cases = [
        {
            'name': 'Minimal feedback payload',
            'payload': {
                'trace_id': 'test-trace-123',
                'rating': 5,
                'feedback_type': 'clarity'
            }
        },
        {
            'name': 'Feedback with comment',
            'payload': {
                'trace_id': 'test-trace-123',
                'rating': 5,
                'feedback_type': 'clarity',
                'comment': 'Great response'
            }
        },
        {
            'name': 'Query with minimal data',
            'payload': {
                'query': 'Test query',
                'jurisdiction_hint': 'India',
                'domain_hint': 'criminal',
                'user_context': {'role': 'citizen', 'confidence_required': True}
            }
        },
        {
            'name': 'Multi-jurisdiction minimal',
            'payload': {
                'query': 'Test query',
                'jurisdictions': ['India']
            }
        },
        {
            'name': 'Explain reasoning minimal',
            'payload': {
                'trace_id': 'test-trace-123',
                'explanation_level': 'brief'
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        endpoint = ''
        if 'rating' in test_case['payload']:
            endpoint = 'feedback'
        elif 'jurisdictions' in test_case['payload']:
            endpoint = 'multi_jurisdiction'
        elif 'explanation_level' in test_case['payload']:
            endpoint = 'explain_reasoning'
        else:
            endpoint = 'query'
        
        url = f'http://localhost:8000/nyaya/{endpoint}?nonce={nonce}'
        
        # Get fresh nonce for each test to avoid reuse issues
        fresh_nonce_resp = requests.get('http://localhost:8000/debug/generate-nonce')
        fresh_nonce = fresh_nonce_resp.json()['nonce']
        url = f'http://localhost:8000/nyaya/{endpoint}?nonce={fresh_nonce}'
        
        headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(url, json=test_case['payload'], headers=headers)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 422:
            print("422 ERROR DETECTED!")
            error_response = response.json()
            print(json.dumps(error_response, indent=2))
            
            # Parse validation errors if present
            if 'detail' in error_response and isinstance(error_response['detail'], list):
                print("\nValidation Error Details:")
                for error in error_response['detail']:
                    loc = error.get('loc', [])
                    msg = error.get('msg', 'Unknown message')
                    error_type = error.get('type', 'Unknown type')
                    print(f"  Location: {loc}")
                    print(f"  Message: {msg}")
                    print(f"  Type: {error_type}")
                    print()
        elif response.status_code != 200:
            print(f"Other error ({response.status_code}):")
            print(json.dumps(response.json(), indent=2))
        else:
            print("SUCCESS")

def test_with_invalid_data():
    print("\n=== Testing with intentionally invalid data ===")
    
    # Get fresh nonce
    nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
    nonce = nonce_response.json()['nonce']
    
    # Test invalid payloads that should definitely cause 422
    invalid_cases = [
        {
            'name': 'Feedback with invalid rating',
            'endpoint': 'feedback',
            'payload': {
                'trace_id': 'test-trace-123',
                'rating': 10,  # Invalid: should be 1-5
                'feedback_type': 'clarity'
            }
        },
        {
            'name': 'Feedback with missing required field',
            'endpoint': 'feedback',
            'payload': {
                'trace_id': 'test-trace-123',
                'feedback_type': 'clarity'
                # Missing 'rating' field
            }
        },
        {
            'name': 'Query with invalid enum',
            'endpoint': 'query',
            'payload': {
                'query': 'Test query',
                'jurisdiction_hint': 'InvalidJurisdiction',
                'domain_hint': 'criminal',
                'user_context': {'role': 'citizen', 'confidence_required': True}
            }
        },
        {
            'name': 'Multi-jurisdiction with empty array',
            'endpoint': 'multi_jurisdiction',
            'payload': {
                'query': 'Test query',
                'jurisdictions': []
            }
        }
    ]
    
    for test_case in invalid_cases:
        print(f"\n--- Testing invalid data: {test_case['name']} ---")
        
        # Get fresh nonce for this test
        fresh_nonce_resp = requests.get('http://localhost:8000/debug/generate-nonce')
        fresh_nonce = fresh_nonce_resp.json()['nonce']
        
        url = f'http://localhost:8000/nyaya/{test_case["endpoint"]}?nonce={fresh_nonce}'
        headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(url, json=test_case['payload'], headers=headers)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 422:
            print("422 ERROR DETECTED (as expected)!")
            error_response = response.json()
            print(json.dumps(error_response, indent=2))
        else:
            print(f"Unexpected status ({response.status_code})")

if __name__ == "__main__":
    reproduce_422_error()
    test_with_invalid_data()