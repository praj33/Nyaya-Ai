"""
Test commercial queries for India, UK, UAE
"""
import requests

BASE_URL = "http://localhost:8000"

test_queries = [
    {
        "name": "Commercial - India (Contract breach)",
        "payload": {
            "query": "my business partner breached our contract",
            "jurisdiction_hint": "India",
            "domain_hint": "commercial",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    },
    {
        "name": "Commercial - India (Company dispute)",
        "payload": {
            "query": "dispute with company shareholders",
            "jurisdiction_hint": "India",
            "domain_hint": "commercial",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    },
    {
        "name": "Commercial - UK (Contract breach)",
        "payload": {
            "query": "my business partner breached our contract",
            "jurisdiction_hint": "UK",
            "domain_hint": "commercial",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    },
    {
        "name": "Commercial - UK (Company dispute)",
        "payload": {
            "query": "dispute with company shareholders",
            "jurisdiction_hint": "UK",
            "domain_hint": "commercial",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    },
    {
        "name": "Commercial - UAE (Contract breach)",
        "payload": {
            "query": "my business partner breached our contract",
            "jurisdiction_hint": "UAE",
            "domain_hint": "commercial",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    },
    {
        "name": "Commercial - UAE (Company dispute)",
        "payload": {
            "query": "dispute with company shareholders",
            "jurisdiction_hint": "UAE",
            "domain_hint": "commercial",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    }
]

def check_server():
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_commercial():
    print("=" * 100)
    print("COMMERCIAL QUERIES VERIFICATION")
    print("=" * 100)
    
    if not check_server():
        print("\n[ERROR] Server not running. Start with: cd Nyaya_AI && start_backend.bat")
        return
    
    print("\n[OK] Server is running\n")
    
    for test in test_queries:
        print("\n" + "=" * 100)
        print(f"TEST: {test['name']}")
        print("=" * 100)
        print(f"Query: {test['payload']['query']}")
        print(f"Jurisdiction: {test['payload']['jurisdiction_hint']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/nyaya/query",
                json=test['payload'],
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\nJurisdiction Detected: {data.get('jurisdiction_detected', 'N/A')}")
                print(f"Domain: {data.get('domain', 'N/A')}")
                print(f"Confidence: {data.get('confidence', {}).get('overall', 0):.2f}")
                
                statutes = data.get('statutes', [])
                print(f"\nStatutes Found: {len(statutes)}")
                
                if statutes:
                    print("\nSTATUTE DETAILS:")
                    for i, statute in enumerate(statutes, 1):
                        print(f"\n  [{i}] {statute.get('act', 'N/A')} ({statute.get('year', 'N/A')})")
                        print(f"      Section: {statute.get('section', 'N/A')}")
                        print(f"      Title: {statute.get('title', 'N/A')[:150]}...")
                else:
                    print("\n  [WARNING] No statutes found!")
                
            else:
                print(f"\n[ERROR] HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except Exception as e:
            print(f"\n[ERROR] Exception: {str(e)}")
    
    print("\n" + "=" * 100)
    print("VERIFICATION COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    test_commercial()
