import requests
import json

def quick_trace_test():
    """Quick test of trace endpoint - execute immediately after getting nonce."""
    
    print("=== Quick Trace Endpoint Test ===\n")
    
    # Step 1: Get nonce and immediately use it
    print("1. Getting nonce and making query request...")
    
    response = requests.get('http://localhost:8000/debug/generate-nonce')
    nonce = response.json()['nonce']
    print(f"   Got nonce: {nonce}")
    
    # Immediate query request
    query_payload = {
        'query': 'What are fundamental rights?',
        'user_context': {'role': 'citizen', 'confidence_required': True}
    }
    
    query_response = requests.post(
        f'http://localhost:8000/nyaya/query?nonce={nonce}',
        json=query_payload
    )
    
    print(f"   Query status: {query_response.status_code}")
    
    if query_response.status_code != 200:
        print(f"   Query failed: {query_response.text}")
        return
    
    query_data = query_response.json()
    trace_id = query_data.get('trace_id')
    print(f"   Generated trace_id: {trace_id}")
    
    # Step 2: Immediately test trace endpoint
    print(f"\n2. Testing trace endpoint...")
    
    trace_response = requests.get(f'http://localhost:8000/nyaya/trace/{trace_id}')
    print(f"   Trace status: {trace_response.status_code}")
    
    if trace_response.status_code == 200:
        trace_data = trace_response.json()
        print("   ✓ Trace endpoint working!")
        print(f"   Trace ID: {trace_data.get('trace_id')}")
        print(f"   Event count: {len(trace_data.get('event_chain', []))}")
        print(f"   Jurisdictions: {trace_data.get('jurisdiction_hops')}")
    else:
        print(f"   ✗ Trace failed: {trace_response.text}")
        # Let's check what's in the ledger
        print("\n3. Checking ledger contents...")
        try:
            with open('provenance_ledger.json', 'r') as f:
                ledger = json.load(f)
                print(f"   Ledger entries: {len(ledger)}")
                for entry in ledger:
                    print(f"   Entry {entry['index']}: {entry.get('signed_event', 'No event')}")
        except Exception as e:
            print(f"   Error reading ledger: {e}")

if __name__ == "__main__":
    quick_trace_test()