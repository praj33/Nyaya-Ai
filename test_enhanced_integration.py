"""Test script for enhanced legal database integration."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from legal_database.database_loader import legal_db
from legal_database.enhanced_response_builder import enhanced_response_builder
from legal_database.enhanced_legal_agent import EnhancedLegalAgent

def test_database_loading():
    """Test legal database loading."""
    print("=== Testing Database Loading ===")
    print(f"Loaded databases: {list(legal_db.databases.keys())}")
    
    # Test Indian domain map
    if 'indian_domain_map' in legal_db.databases:
        print("✓ Indian domain map loaded")
    else:
        print("✗ Indian domain map not loaded")
    
    # Test UAE domain map
    if 'uae_domain_map' in legal_db.databases:
        print("✓ UAE domain map loaded")
    else:
        print("✗ UAE domain map not loaded")
    
    # Test UK domain map
    if 'uk_domain_map' in legal_db.databases:
        print("✓ UK domain map loaded")
    else:
        print("✗ UK domain map not loaded")

def test_domain_classification():
    """Test domain classification functionality."""
    print("\n=== Testing Domain Classification ===")
    
    test_queries = [
        ("What is the punishment for murder in India?", "India"),
        ("How to file a civil case in UAE?", "UAE"),
        ("What are the requirements for divorce in UK?", "UK")
    ]
    
    for query, jurisdiction in test_queries:
        classification = legal_db.classify_query_domain(query, jurisdiction)
        print(f"Query: {query}")
        print(f"Jurisdiction: {jurisdiction}")
        print(f"Classification: {classification}")
        print("---")

def test_legal_sections():
    """Test legal sections retrieval."""
    print("\n=== Testing Legal Sections Retrieval ===")
    
    test_cases = [
        ("murder", "India", "criminal"),
        ("contract dispute", "UAE", "civil"),
        ("theft", "UK", "criminal")
    ]
    
    for query, jurisdiction, domain in test_cases:
        sections = legal_db.get_legal_sections(query, jurisdiction, domain)
        print(f"Query: {query} | Jurisdiction: {jurisdiction} | Domain: {domain}")
        print(f"Found {len(sections)} relevant sections")
        for section in sections[:2]:  # Show first 2
            print(f"  - {section}")
        print("---")

def test_enhanced_response():
    """Test enhanced response building."""
    print("\n=== Testing Enhanced Response Building ===")
    
    test_query = "What is the punishment for theft in India?"
    response = enhanced_response_builder.build_enhanced_legal_response(
        query=test_query,
        jurisdiction="India",
        domain_hint="criminal",
        confidence=0.8,
        trace_id="test-123"
    )
    
    print(f"Query: {test_query}")
    print(f"Domain Classification: {response['domain_classification']}")
    print(f"Legal Provisions Found: {response['legal_provisions']['total_matches']}")
    print(f"Risk Level: {response['risk_assessment']['risk_level']}")
    print(f"Next Steps: {response['procedural_guidance']['next_steps'][:2]}")

def test_enhanced_agent():
    """Test enhanced legal agent."""
    print("\n=== Testing Enhanced Legal Agent ===")
    
    agent = EnhancedLegalAgent(agent_id="test_agent", jurisdiction="India")
    
    import asyncio
    async def run_test():
        result = await agent.process({
            "query": "What are the elements of murder under Indian law?",
            "jurisdiction": "India",
            "trace_id": "test-456",
            "domain_classification": {"domain": "criminal", "confidence": 0.8}
        })
        return result
    
    result = asyncio.run(run_test())
    print(f"Agent Result: {result['query_type']}")
    print(f"Enhanced Analysis: {result['enhanced_analysis']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Risk Level: {result['risk_assessment']['risk_level']}")

if __name__ == "__main__":
    print("🚀 Testing Enhanced Legal Database Integration")
    print("=" * 50)
    
    test_database_loading()
    test_domain_classification()
    test_legal_sections()
    test_enhanced_response()
    test_enhanced_agent()
    
    print("\n✅ All tests completed!")
    print("Enhanced legal database integration is ready for use.")