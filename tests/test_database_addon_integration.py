#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.ontology.statute_resolver import StatuteResolver

def test_database_addon_integration():
    """Test that addon offense subtypes are now in main database"""
    resolver = StatuteResolver()
    
    # Test cyber bullying
    result = resolver.resolve_query("Someone is cyber bullying me online")
    print(f"Cyber bullying result: {result}")
    assert any("Information Technology Act" in str(s) for s in result.get('statutes', []))
    
    # Test workplace harassment
    result = resolver.resolve_query("My boss is touching me inappropriately")
    print(f"Workplace harassment result: {result}")
    assert any("74" in str(s) for s in result.get('statutes', []))
    
    # Test human trafficking
    result = resolver.resolve_query("Girl was trafficked for prostitution")
    print(f"Human trafficking result: {result}")
    assert any("143" in str(s) for s in result.get('statutes', []))
    
    print("Database addon integration tests passed!")

if __name__ == "__main__":
    test_database_addon_integration()