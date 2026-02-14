import requests
import json

def test_murder_query():
    url = "http://localhost:8000/nyaya/query"
    
    payload = {
        "query": "someone killed my friend",
        "jurisdiction_hint": "India",
        "domain_hint": "criminal",
        "user_context": {
            "role": "citizen",
            "confidence_required": True
        }
    }
    
    print("=" * 80)
    print("TESTING MURDER/KILLING QUERY")
    print("=" * 80)
    print(f"\nQuery: {payload['query']}")
    print(f"Jurisdiction: {payload['jurisdiction_hint']}")
    print(f"Domain: {payload['domain_hint']}")
    
    response = requests.post(url, json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n" + "=" * 80)
        print("RESPONSE DETAILS")
        print("=" * 80)
        
        print(f"\nDomain: {result.get('domain')}")
        print(f"Jurisdiction: {result.get('jurisdiction')}")
        print(f"Enforcement Decision: {result.get('enforcement_decision')}")
        
        statutes = result.get("statutes", [])
        print(f"\n[STATUTES] Found {len(statutes)} statutes:")
        for statute in statutes:
            print(f"  - {statute.get('act')} ({statute.get('year')})")
            print(f"    Section {statute.get('section')}: {statute.get('title')}")
        
        constitutional_articles = result.get("constitutional_articles", [])
        if constitutional_articles:
            print(f"\n[CONSTITUTIONAL ARTICLES] {len(constitutional_articles)} articles:")
            for article in constitutional_articles:
                print(f"  - {article}")
        
        timeline = result.get("timeline", [])
        if timeline:
            print(f"\n[TIMELINE] {len(timeline)} steps:")
            for step in timeline:
                print(f"  - {step.get('step')}: {step.get('eta')}")
        
        evidence = result.get("evidence_requirements", [])
        if evidence:
            print(f"\n[EVIDENCE REQUIREMENTS] {len(evidence)} items:")
            for item in evidence:
                print(f"  - {item}")
        
        reasoning = result.get("reasoning_trace", {})
        print(f"\n[REASONING]")
        print(f"  Sections found: {reasoning.get('sections_found')}")
        print(f"  Confidence: {result.get('confidence', {}).get('overall')}")
        
        procedural_steps = reasoning.get("procedural_steps", [])
        if procedural_steps:
            print(f"\n[PROCEDURAL STEPS] {len(procedural_steps)} steps:")
            for i, step in enumerate(procedural_steps[:5], 1):
                print(f"  {i}. {step}")
        
        remedies = reasoning.get("remedies", [])
        if remedies:
            print(f"\n[REMEDIES] {len(remedies)} remedies:")
            for i, remedy in enumerate(remedies[:5], 1):
                print(f"  {i}. {remedy}")
        
        print("\n" + "=" * 80)
        print("FULL JSON RESPONSE")
        print("=" * 80)
        print(json.dumps(result, indent=2))
        
    else:
        print(f"\n[ERROR] Request failed")
        print(response.text)

if __name__ == "__main__":
    test_murder_query()
