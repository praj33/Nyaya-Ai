import requests
import json

def test_feedback_validation():
    print("=== Detailed Feedback Endpoint Validation Test ===")
    
    # Get fresh nonce
    response = requests.get('http://localhost:8000/debug/generate-nonce')
    nonce = response.json()['nonce']
    print(f"Nonce: {nonce}")
    
    # Test the feedback endpoint
    url = f'http://localhost:8000/nyaya/feedback?nonce={nonce}'
    payload = {
        'trace_id': 'test-trace-123',
        'rating': 5,
        'feedback_type': 'clarity',
        'comment': 'Great response'
    }
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print("Error Response:")
        error_data = response.json()
        print(json.dumps(error_data, indent=2))
        
        # Check if it's a validation error
        if 'detail' in error_data:
            detail = error_data['detail']
            if isinstance(detail, list):
                print("\nValidation Errors Found:")
                for error in detail:
                    print(f"  - Location: {error.get('loc', 'N/A')}")
                    print(f"    Message: {error.get('msg', 'N/A')}")
                    print(f"    Type: {error.get('type', 'N/A')}")
            elif isinstance(detail, dict):
                print("\nError Details:")
                print(json.dumps(detail, indent=2))
    else:
        print("Success Response:")
        print(json.dumps(response.json(), indent=2))

def test_all_endpoints_detailed():
    print("\n=== Testing All Endpoints with Detailed Error Capture ===")
    endpoints = [
        ('query', {
            'query': 'Test query',
            'jurisdiction_hint': 'India',
            'domain_hint': 'criminal',
            'user_context': {'role': 'citizen', 'confidence_required': True}
        }),
        ('multi_jurisdiction', {
            'query': 'Test query',
            'jurisdictions': ['India', 'UK']
        }),
        ('explain_reasoning', {
            'trace_id': 'test-trace-123',
            'explanation_level': 'brief'
        }),
        ('feedback', {
            'trace_id': 'test-trace-123',
            'rating': 5,
            'feedback_type': 'clarity',
            'comment': 'Great response'
        })
    ]
    
    results = []
    
    for endpoint, payload in endpoints:
        print(f"\n--- Testing {endpoint} endpoint ---")
        
        # Get fresh nonce
        response = requests.get('http://localhost:8000/debug/generate-nonce')
        nonce = response.json()['nonce']
        print(f"Nonce: {nonce}")
        
        # Make request
        url = f'http://localhost:8000/nyaya/{endpoint}?nonce={nonce}'
        headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(url, json=payload, headers=headers)
        
        # Store result
        success = response.status_code == 200
        results.append({
            'endpoint': endpoint,
            'status': response.status_code,
            'success': success,
            'response': response.json() if response.status_code != 200 else None
        })
        
        print(f"Status: {response.status_code}")
        if not success:
            print("Error Response:")
            print(json.dumps(response.json(), indent=2))
    
    # Print summary
    print("\n=== Summary ===")
    all_passed = True
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{result['endpoint']}: {status} ({result['status']})")
        if not result['success']:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All endpoints are working correctly!")
    else:
        print("\n❌ Some endpoints have validation issues!")
        print("\nDetailed Error Analysis:")
        for result in results:
            if not result['success']:
                print(f"\n{result['endpoint']} endpoint errors:")
                if result['response']:
                    print(json.dumps(result['response'], indent=2))
    
    return all_passed

if __name__ == "__main__":
    test_feedback_validation()
    test_all_endpoints_detailed()