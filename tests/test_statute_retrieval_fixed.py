#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.ontology.statute_resolver import StatuteResolver

def test_dowry_harassment_statutes():
    """Test dowry harassment query returns statutes"""
    resolver = StatuteResolver()
    
    query = "dowry harassment"
    result = resolver.resolve_query(query, ["criminal"], "IN")
    
    print(f"Query: {query}")
    print(f"Statutes found: {len(result['statutes'])}")
    
    if result['statutes']:
        for i, statute in enumerate(result['statutes'][:3]):
            print(f"  {i+1}. {statute['act']} Section {statute['section']}: {statute['title']}")
    
    assert len(result['statutes']) > 0, "Expected statutes for dowry harassment"
    print("✓ Dowry harassment test passed")

def test_murder_statutes():
    """Test murder query returns statutes"""
    resolver = StatuteResolver()
    
    query = "murder"
    result = resolver.resolve_query(query, ["criminal"], "IN")
    
    print(f"Query: {query}")
    print(f"Statutes found: {len(result['statutes'])}")
    
    if result['statutes']:
        for i, statute in enumerate(result['statutes'][:3]):
            print(f"  {i+1}. {statute['act']} Section {statute['section']}: {statute['title']}")
    
    assert len(result['statutes']) > 0, "Expected statutes for murder"
    print("✓ Murder test passed")

def test_statute_dataset_loaded():
    """Test statute dataset is loaded"""
    resolver = StatuteResolver()
    
    print(f"Statute dataset size: {len(resolver.sections)}")
    print(f"Acts loaded: {len(resolver.acts)}")
    
    assert len(resolver.sections) > 0, "Statute dataset should be loaded"
    print("✓ Dataset loaded test passed")

if __name__ == "__main__":
    print("Testing statute retrieval...")
    test_statute_dataset_loaded()
    test_dowry_harassment_statutes()
    test_murder_statutes()
    print("All statute retrieval tests completed!")