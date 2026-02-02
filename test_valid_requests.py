import requests
import json

def test_valid_requests():
    """Test all endpoints with valid requests to ensure they work correctly."""
    
    print("=== Testing Valid Requests Across All Endpoints ===\n")
    
    endpoints = ['query', 'multi_jurisdiction', 'explain_reasoning', 'feedback']
    results = []
    
    for endpoint in endpoints:
        print(f"Testing {endpoint} endpoint...")
        
        # Get fresh nonce
        nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
        nonce = nonce_response.json()['nonce']
        
        # Build valid payload for each endpoint
        if endpoint == 'query':
            payload = {
                'query': 'What are fundamental rights?',
                'user_context': {'role': 'citizen', 'confidence_required': True}
            }
        elif endpoint == 'multi_jurisdiction':
            payload = {
                'query': 'What is the punishment for theft?',
                'jurisdictions': ['India', 'UK']
            }
        elif endpoint == 'explain_reasoning':
            payload = {
                'trace_id': 'test-trace-123',
                'explanation_level': 'brief'
            }
        elif endpoint == 'feedback':
            payload = {
                'trace_id': 'test-trace-123',
                'rating': 4,
                'feedback_type': 'clarity'
            }
        
        # Make request
        url = f'http://localhost:8000/nyaya/{endpoint}?nonce={nonce}'
        response = requests.post(url, json=payload)
        
        result = {
            'endpoint': endpoint,
            'status_code': response.status_code,
            'success': response.status_code == 200,
            'response': response.json() if response.status_code == 200 else response.text
        }
        results.append(result)
        
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✓ Success")
            if endpoint == 'query':
                print(f"    Trace ID: {response.json().get('trace_id')}")
        elif response.status_code == 422:
            print(f"  ✗ 422 Validation Error")
            error_detail = response.json()
            print(f"    Error: {json.dumps(error_detail, indent=4)}")
        else:
            print(f"  Other error: {response.status_code}")
            print(f"  Response: {response.text}")
        print()
    
    # Summary
    print("=== Summary ===")
    successful = sum(1 for r in results if r['success'])
    print(f"Successful endpoints: {successful}/4")
    
    for result in results:
        status = "✓" if result['success'] else "✗"
        print(f"{status} {result['endpoint']}: {result['status_code']}")
    
    return successful == 4

if __name__ == "__main__":
    all_successful = test_valid_requests()
    if all_successful:
        print("\n🎉 All endpoints working correctly with valid requests!")
    else:
        print("\n❌ Some endpoints still have issues with valid requests")