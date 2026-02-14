import sys
sys.path.append('.')

from clean_legal_advisor import EnhancedLegalAdvisor, LegalQuery
from api.router import query_legal
from api.schemas import QueryRequest, UserContext, UserRole, JurisdictionHint, DomainHint
import asyncio
import json

async def test_procedural_steps_in_api():
    print("=" * 80)
    print("TESTING PROCEDURAL STEPS IN API RESPONSE")
    print("=" * 80)
    
    request = QueryRequest(
        query="someone killed my friend",
        jurisdiction_hint=JurisdictionHint.INDIA,
        domain_hint=DomainHint.CRIMINAL,
        user_context=UserContext(role=UserRole.CITIZEN, confidence_required=True)
    )
    
    response = await query_legal(request)
    
    print(f"\nQuery: {request.query}")
    print(f"\n[RESPONSE STRUCTURE]")
    print(f"Domain: {response.domain}")
    print(f"Jurisdiction: {response.jurisdiction}")
    
    print(f"\n[STATUTES] {len(response.statutes)} found:")
    for statute in response.statutes:
        print(f"  - {statute.act} Section {statute.section}: {statute.title}")
    
    print(f"\n[REASONING TRACE]")
    reasoning = response.reasoning_trace
    
    if "procedural_steps" in reasoning:
        steps = reasoning["procedural_steps"]
        print(f"Procedural Steps: {len(steps)} steps found")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
    else:
        print("ERROR: procedural_steps NOT FOUND in reasoning_trace")
    
    if "remedies" in reasoning:
        remedies = reasoning["remedies"]
        print(f"\nRemedies: {len(remedies)} remedies found")
        for i, remedy in enumerate(remedies, 1):
            print(f"  {i}. {remedy}")
    else:
        print("ERROR: remedies NOT FOUND in reasoning_trace")
    
    print(f"\n[FULL REASONING_TRACE KEYS]")
    print(f"Keys: {list(reasoning.keys())}")
    
    print("\n" + "=" * 80)
    print("FULL JSON RESPONSE")
    print("=" * 80)
    print(json.dumps(response.dict(), indent=2))

if __name__ == "__main__":
    asyncio.run(test_procedural_steps_in_api())
