import requests
import json

def test_suicide_query():
    url = "http://localhost:8000/nyaya/query"
    
    payload = {
        "query": "my friend suicide",
        "jurisdiction_hint": "India",
        "domain_hint": "criminal",
        "user_context": {
            "role": "citizen",
            "confidence_required": True
        }
    }
    
    response = requests.post(url, json=payload)
    
    print("Status Code:", response.status_code)
    print("\nResponse JSON:")
    result = response.json()
    print(json.dumps(result, indent=2))
    
    # Assertions
    statutes = result.get("statutes", [])
    sections_found = result.get("reasoning_trace", {}).get("sections_found", 0)
    
    print(f"\n✓ Statutes count: {len(statutes)}")
    print(f"✓ Sections found: {sections_found}")
    
    assert len(statutes) >= 1, f"Expected at least 1 statute, got {len(statutes)}"
    assert sections_found >= 1, f"Expected sections_found >= 1, got {sections_found}"
    
    # Check for BNS 108 (abetment to suicide)
    has_108 = any(s.get("section") == "108" for s in statutes)
    print(f"✓ Has BNS 108 (abetment to suicide): {has_108}")
    
    print("\n✅ Test passed!")

if __name__ == "__main__":
    test_suicide_query()
