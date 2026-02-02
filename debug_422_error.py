import requests
import json

def debug_422_error():
    """Debug the 422 validation error on feedback endpoint."""
    
    print("=== Debugging 422 Validation Error ===\n")
    
    # Step 1: Get a valid nonce
    print("1. Getting valid nonce...")
    nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
    nonce = nonce_response.json()['nonce']
    print(f"   Got nonce: {nonce}")
    
    # Step 2: Test various feedback payloads to identify the validation issue
    print("\n2. Testing feedback endpoint with different payloads...")
    
    # Test cases with different potential issues
    test_cases = [
        {
            "name": "Valid payload",
            "payload": {
                "trace_id": "test-trace-123",
                "rating": 3,
                "feedback_type": "clarity"
            }
        },
        {
            "name": "Missing required field - trace_id",
            "payload": {
                "rating": 3,
                "feedback_type": "clarity"
            }
        },
        {
            "name": "Missing required field - rating",
            "payload": {
                "trace_id": "test-trace-123",
                "feedback_type": "clarity"
            }
        },
        {
            "name": "Missing required field - feedback_type",
            "payload": {
                "trace_id": "test-trace-123",
                "rating": 3
            }
        },
        {
            "name": "Invalid rating (too low)",
            "payload": {
                "trace_id": "test-trace-123",
                "rating": 0,
                "feedback_type": "clarity"
            }
        },
        {
            "name": "Invalid rating (too high)",
            "payload": {
                "trace_id": "test-trace-123",
                "rating": 6,
                "feedback_type": "clarity"
            }
        },
        {
            "name": "Invalid feedback_type",
            "payload": {
                "trace_id": "test-trace-123",
                "rating": 3,
                "feedback_type": "invalid_type"
            }
        },
        {
            "name": "With comment",
            "payload": {
                "trace_id": "test-trace-123",
                "rating": 4,
                "feedback_type": "usefulness",
                "comment": "This is a test comment"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test_case['name']}")
        print(f"   Payload: {json.dumps(test_case['payload'], indent=6)}")
        
        response = requests.post(
            f'http://localhost:8000/nyaya/feedback?nonce={nonce}',
            json=test_case['payload']
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 422:
            error_detail = response.json()
            print(f"   422 Error Detail: {json.dumps(error_detail, indent=6)}")
        elif response.status_code == 200:
            print(f"   ✓ Success: {response.json()}")
        else:
            print(f"   Other Error: {response.text}")
        
        # Get fresh nonce for next test (since nonces can only be used once)
        nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
        nonce = nonce_response.json()['nonce']

if __name__ == "__main__":
    debug_422_error()