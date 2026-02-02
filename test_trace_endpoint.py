import requests
import json
import time

def test_trace_endpoint():
    """Test the trace endpoint with actual trace data."""
    
    print("=== Testing Trace Endpoint ===\n")
    
    # Step 1: Generate a trace by making a query request
    print("1. Generating trace data via query endpoint...")
    
    # Get nonce
    nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
    nonce = nonce_response.json()['nonce']
    print(f"   Got nonce: {nonce}")
    
    # Make query request to generate trace
    query_payload = {
        'query': 'What are the fundamental rights under the Indian Constitution?',
        'user_context': {'role': 'citizen', 'confidence_required': True}
    }
    
    query_response = requests.post(
        f'http://localhost:8000/nyaya/query?nonce={nonce}',
        json=query_payload
    )
    
    print(f"   Query response status: {query_response.status_code}")
    if query_response.status_code == 200:
        query_data = query_response.json()
        trace_id = query_data.get('trace_id')
        print(f"   Generated trace_id: {trace_id}")
    else:
        print(f"   Query failed: {query_response.text}")
        return
    
    # Step 2: Test the trace endpoint with the generated trace_id
    print(f"\n2. Testing trace endpoint with trace_id: {trace_id}")
    
    trace_response = requests.get(f'http://localhost:8000/nyaya/trace/{trace_id}')
    
    print(f"   Trace response status: {trace_response.status_code}")
    
    if trace_response.status_code == 200:
        trace_data = trace_response.json()
        print("   Trace data retrieved successfully!")
        print(f"   Trace ID: {trace_data.get('trace_id')}")
        print(f"   Event chain length: {len(trace_data.get('event_chain', []))}")
        print(f"   Agent routing tree: {trace_data.get('agent_routing_tree')}")
        print(f"   Jurisdiction hops: {trace_data.get('jurisdiction_hops')}")
        print(f"   Nonce verification: {trace_data.get('nonce_verification')}")
        print(f"   Signature verification: {trace_data.get('signature_verification')}")
    else:
        print(f"   Trace endpoint failed: {trace_response.text}")
        print(f"   Response headers: {dict(trace_response.headers)}")
    
    # Step 3: Test with non-existent trace ID
    print(f"\n3. Testing trace endpoint with non-existent trace ID...")
    
    fake_trace_id = "non-existent-trace-123"
    fake_response = requests.get(f'http://localhost:8000/nyaya/trace/{fake_trace_id}')
    
    print(f"   Fake trace response status: {fake_response.status_code}")
    if fake_response.status_code == 404:
        print("   ✓ Correctly returns 404 for non-existent trace")
        error_data = fake_response.json()
        print(f"   Error message: {error_data.get('message')}")
    else:
        print(f"   ✗ Unexpected response: {fake_response.status_code}")
        print(f"   Response: {fake_response.text}")

    # Step 4: Test with invalid trace ID format
    print(f"\n4. Testing trace endpoint with invalid trace ID format...")
    
    invalid_trace_id = "invalid-format"
    invalid_response = requests.get(f'http://localhost:8000/nyaya/trace/{invalid_trace_id}')
    
    print(f"   Invalid trace response status: {invalid_response.status_code}")
    if invalid_response.status_code == 404:
        print("   ✓ Correctly returns 404 for invalid trace ID")
    else:
        print(f"   Response: {invalid_response.text}")

if __name__ == "__main__":
    test_trace_endpoint()