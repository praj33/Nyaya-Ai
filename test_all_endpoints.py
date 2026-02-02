import requests
import json

def test_all_endpoints():
    print("=== Testing All Endpoints ===")
    endpoints = ['query', 'multi_jurisdiction', 'explain_reasoning', 'feedback']
    results = []
    
    for endpoint in endpoints:
        # Get fresh nonce
        response = requests.get('http://localhost:8000/debug/generate-nonce')
        nonce = response.json()['nonce']
        
        # Build URL
        url = f'http://localhost:8000/nyaya/{endpoint}?nonce={nonce}'
        
        # Build payload based on endpoint
        if endpoint == 'query':
            payload = {
                'query': 'Test query',
                'jurisdiction_hint': 'India',
                'domain_hint': 'criminal',
                'user_context': {'role': 'citizen', 'confidence_required': True}
            }
        elif endpoint == 'multi_jurisdiction':
            payload = {
                'query': 'Test query',
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
                'rating': 5,
                'feedback_type': 'clarity',
                'comment': 'Great response'
            }
        
        # Make request
        headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.post(url, json=payload, headers=headers)
        
        # Store result
        success = response.status_code == 200
        results.append({
            'endpoint': endpoint,
            'status': response.status_code,
            'success': success
        })
        
        print(f'{endpoint}: {response.status_code}')
        if not success:
            print(json.dumps(response.json(), indent=2))
        print()
    
    # Print summary
    print("=== Summary ===")
    all_passed = True
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{result['endpoint']}: {status} ({result['status']})")
        if not result['success']:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All endpoints are working correctly!")
    else:
        print("\n❌ Some endpoints have issues!")
    
    return all_passed

if __name__ == "__main__":
    test_all_endpoints()