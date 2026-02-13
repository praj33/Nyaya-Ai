#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from api.router import router
from api.schemas import QueryRequest, UserContext
import asyncio

async def test_statute_retrieval():
    """Test that statutes appear for criminal queries"""
    
    test_cases = [
        {
            "query": "i robbed a bank",
            "expected_min_statutes": 1
        },
        {
            "query": "my friend suicide", 
            "expected_min_statutes": 1
        }
    ]
    
    print("Testing statute retrieval for criminal queries...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test_case['query']}'")
        
        request = QueryRequest(
            query=test_case['query'],
            user_context=UserContext(role="citizen")
        )
        
        try:
            response = await router.query_legal(request)
            
            statutes_count = len(response.statutes)
            print(f"Statutes found: {statutes_count}")
            
            if statutes_count >= test_case['expected_min_statutes']:
                print("✅ PASS")
            else:
                print("❌ FAIL - No statutes returned")
                
            # Print first few statutes for verification
            for j, statute in enumerate(response.statutes[:3], 1):
                print(f"  {j}. {statute.act} Section {statute.section}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_statute_retrieval())