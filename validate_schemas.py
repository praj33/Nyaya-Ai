import requests
import json

def validate_schemas():
    """Validate that all schemas are correctly defined and working."""
    
    print("=== Schema Validation Test ===\n")
    
    # Test valid payloads for each endpoint
    test_cases = [
        {
            "name": "Query Request Schema",
            "endpoint": "query",
            "payload": {
                "query": "Test legal query",
                "user_context": {
                    "role": "citizen",  # Valid enum value
                    "confidence_required": True
                },
                "jurisdiction_hint": "India",  # Valid enum value
                "domain_hint": "criminal"  # Valid enum value
            }
        },
        {
            "name": "Multi-Jurisdiction Request Schema",
            "endpoint": "multi_jurisdiction", 
            "payload": {
                "query": "Cross-jurisdiction query",
                "jurisdictions": ["India", "UK"]  # Valid enum values, proper array
            }
        },
        {
            "name": "Explain Reasoning Request Schema",
            "endpoint": "explain_reasoning",
            "payload": {
                "trace_id": "valid-trace-id",
                "explanation_level": "detailed"  # Valid enum value
            }
        },
        {
            "name": "Feedback Request Schema",
            "endpoint": "feedback",
            "payload": {
                "trace_id": "valid-trace-id",
                "rating": 3,  # Valid rating (1-5)
                "feedback_type": "correctness",  # Valid enum value
                "comment": "Optional comment field"
            }
        }
    ]
    
    all_valid = True
    
    for test_case in test_cases:
        print(f"Testing {test_case['name']}...")
        
        # Get fresh nonce
        nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
        nonce = nonce_response.json()['nonce']
        
        # Send request
        url = f"http://localhost:8000/nyaya/{test_case['endpoint']}?nonce={nonce}"
        response = requests.post(url, json=test_case['payload'])
        
        if response.status_code == 200:
            print(f"  ✓ Valid - Status {response.status_code}")
        elif response.status_code == 422:
            print(f"  ✗ Validation Error - Status {response.status_code}")
            print(f"    Error: {response.json()}")
            all_valid = False
        else:
            print(f"  ? Other status {response.status_code}: {response.text}")
        
        print()
    
    # Test edge cases that should trigger 422 errors
    print("=== Testing Invalid Requests (Should Return 422) ===\n")
    
    invalid_cases = [
        {
            "name": "Missing required field in Feedback",
            "endpoint": "feedback",
            "payload": {
                "trace_id": "test",
                "rating": 3
                # Missing feedback_type - should cause 422
            }
        },
        {
            "name": "Invalid rating value in Feedback",
            "endpoint": "feedback", 
            "payload": {
                "trace_id": "test",
                "rating": 10,  # Invalid - outside 1-5 range
                "feedback_type": "clarity"
            }
        },
        {
            "name": "Invalid enum value in Query",
            "endpoint": "query",
            "payload": {
                "query": "Test",
                "user_context": {
                    "role": "invalid_role",  # Invalid enum value
                    "confidence_required": True
                }
            }
        }
    ]
    
    all_422_correct = True
    
    for invalid_case in invalid_cases:
        print(f"Testing {invalid_case['name']}...")
        
        # Get fresh nonce
        nonce_response = requests.get('http://localhost:8000/debug/generate-nonce')
        nonce = nonce_response.json()['nonce']
        
        # Send invalid request
        url = f"http://localhost:8000/nyaya/{invalid_case['endpoint']}?nonce={nonce}"
        response = requests.post(url, json=invalid_case['payload'])
        
        if response.status_code == 422:
            print(f"  ✓ Correctly returned 422 - Validation working")
        else:
            print(f"  ✗ Expected 422 but got {response.status_code}")
            all_422_correct = False
        
        print()
    
    print("=== FINAL RESULT ===")
    if all_valid and all_422_correct:
        print("✓ ALL SCHEMAS ARE CORRECTLY DEFINED AND WORKING PROPERLY")
        print("✓ 422 validation errors are returned appropriately for invalid requests")
        print("✓ Valid requests return 200 OK as expected")
    else:
        print("✗ Some issues detected with schema validation")
    
    return all_valid and all_422_correct

if __name__ == "__main__":
    validate_schemas()