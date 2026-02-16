"""
Test murder and robbery statutes for India, UK, UAE
"""
import requests
import json

BASE_URL = "http://localhost:8000"

test_queries = [
    # MURDER queries
    {
        "name": "Murder - India",
        "payload": {
            "query": "someone murdered my brother",
            "jurisdiction_hint": "India",
            "domain_hint": "criminal",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    },
    {
        "name": "Murder - UK",
        "payload": {
            "query": "someone murdered my brother",
            "jurisdiction_hint": "UK",
            "domain_hint": "criminal",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    },
    {
        "name": "Murder - UAE",
        "payload": {
            "query": "someone murdered my brother",
            "jurisdiction_hint": "UAE",
            "domain_hint": "criminal",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    },
    # ROBBERY queries
    {
        "name": "Robbery - India",
        "payload": {
            "query": "I was robbed at gunpoint",
            "jurisdiction_hint": "India",
            "domain_hint": "criminal",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    },
    {
        "name": "Robbery - UK",
        "payload": {
            "query": "I was robbed at gunpoint",
            "jurisdiction_hint": "UK",
            "domain_hint": "criminal",
            "user_context": {"role": "citizen", "confidence_required": True}
        }
    },
    {
        "name": "Robbery - UAE",
        "payload": {
            "query": "I was robbed at gunpoint",
            "jurisdiction_hint": "UAE",
            "domain_hint": "criminal",
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

def test_statutes():
    print("=" * 100)
    print("MURDER & ROBBERY STATUTE VERIFICATION")
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
                
                # Check for wrong jurisdiction statutes
                jurisdiction_code = test['payload']['jurisdiction_hint']
                wrong_acts = []
                
                for statute in statutes:
                    act = statute.get('act', '')
                    
                    # India-specific acts
                    if jurisdiction_code != 'India' and any(x in act for x in ['BNS', 'IPC', 'CrPC', 'Indian']):
                        wrong_acts.append(f"{act} (Indian law in {jurisdiction_code} query)")
                    
                    # UK-specific acts
                    if jurisdiction_code != 'UK' and any(x in act for x in ['Offences Act', 'Theft Act', 'Criminal Justice Act']):
                        wrong_acts.append(f"{act} (UK law in {jurisdiction_code} query)")
                    
                    # UAE-specific acts
                    if jurisdiction_code != 'UAE' and any(x in act for x in ['UAE', 'Federal Law']):
                        wrong_acts.append(f"{act} (UAE law in {jurisdiction_code} query)")
                
                if wrong_acts:
                    print("\n  [ERROR] WRONG JURISDICTION STATUTES FOUND:")
                    for wrong in wrong_acts:
                        print(f"    - {wrong}")
                
            else:
                print(f"\n[ERROR] HTTP {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except Exception as e:
            print(f"\n[ERROR] Exception: {str(e)}")
    
    print("\n" + "=" * 100)
    print("VERIFICATION COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    test_statutes()
