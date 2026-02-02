import requests
import json

def test_feedback_endpoint_comprehensive():
    print("=== Comprehensive Feedback Endpoint Test ===")
    
    # Test cases that should work
    valid_test_cases = [
        {
            'name': 'Valid feedback with all fields',
            'payload': {
                'trace_id': 'test-trace-123',
                'rating': 5,
                'feedback_type': 'clarity',
                'comment': 'Great response'
            }
        },
        {
            'name': 'Valid feedback without comment',
            'payload': {
                'trace_id': 'test-trace-456',
                'rating': 3,
                'feedback_type': 'correctness'
            }
        },
        {
            'name': 'Valid feedback with minimum rating',
            'payload': {
                'trace_id': 'test-trace-789',
                'rating': 1,
                'feedback_type': 'usefulness',
                'comment': 'Could be better'
            }
        },
        {
            'name': 'Valid feedback with maximum rating',
            'payload': {
                'trace_id': 'test-trace-999',
                'rating': 5,
                'feedback_type': 'clarity'
            }
        }
    ]
    
    results = []
    
    for test_case in valid_test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")
        
        # Get fresh nonce
        nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
        nonce = nonce_response.json()['nonce']
        print(f"Nonce: {nonce}")
        
        # Make request
        url = f'http://localhost:8000/nyaya/feedback?nonce={nonce}'
        headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(url, json=test_case['payload'], headers=headers)
        
        result = {
            'test_name': test_case['name'],
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'response': response.json() if response.status_code != 200 else None
        }
        results.append(result)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS - Response:")
            print(json.dumps(response.json(), indent=2))
        elif response.status_code == 422:
            print("422 VALIDATION ERROR!")
            error_response = response.json()
            print(json.dumps(error_response, indent=2))
            
            # Detailed error analysis
            if 'detail' in error_response and isinstance(error_response['detail'], list):
                print("\nDetailed Validation Errors:")
                for i, error in enumerate(error_response['detail']):
                    print(f"Error {i+1}:")
                    print(f"  Location: {error.get('loc', 'N/A')}")
                    print(f"  Message: {error.get('msg', 'N/A')}")
                    print(f"  Type: {error.get('type', 'N/A')}")
                    print(f"  Input: {error.get('input', 'N/A')}")
                    print()
        else:
            print(f"Other error ({response.status_code}):")
            print(json.dumps(response.json(), indent=2))
    
    # Summary
    print("\n=== SUMMARY ===")
    passed = 0
    failed = 0
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{result['test_name']}: {status} ({result['status_code']})")
        if result['success']:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nFailed test details:")
        for result in results:
            if not result['success']:
                print(f"\n{result['test_name']}:")
                if result['response']:
                    print(json.dumps(result['response'], indent=2))
    
    return failed == 0

def test_other_endpoints():
    print("\n=== Testing Other Endpoints ===")
    
    endpoints = [
        ('query', {
            'query': 'What is the punishment for theft in India?',
            'jurisdiction_hint': 'India',
            'domain_hint': 'criminal',
            'user_context': {'role': 'citizen', 'confidence_required': True}
        }),
        ('multi_jurisdiction', {
            'query': 'Compare contract law',
            'jurisdictions': ['India', 'UK']
        }),
        ('explain_reasoning', {
            'trace_id': 'test-trace-123',
            'explanation_level': 'brief'
        })
    ]
    
    results = []
    
    for endpoint, payload in endpoints:
        print(f"\n--- Testing {endpoint} endpoint ---")
        
        # Get fresh nonce
        nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
        nonce = nonce_response.json()['nonce']
        
        # Make request
        url = f'http://localhost:8000/nyaya/{endpoint}?nonce={nonce}'
        headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(url, json=payload, headers=headers)
        
        result = {
            'endpoint': endpoint,
            'status_code': response.status_code,
            'success': response.status_code == 200
        }
        results.append(result)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS")
        elif response.status_code == 422:
            print("422 VALIDATION ERROR!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Other error: {response.status_code}")
    
    # Summary
    print("\n=== Other Endpoints Summary ===")
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{result['endpoint']}: {status} ({result['status_code']})")

if __name__ == "__main__":
    feedback_success = test_feedback_endpoint_comprehensive()
    test_other_endpoints()
    
    if feedback_success:
        print("\n🎉 All feedback tests passed!")
    else:
        print("\n❌ Some feedback tests failed!")