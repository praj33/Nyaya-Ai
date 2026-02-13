#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from core.ontology.statute_resolver import StatuteResolver

def test_murder_query():
    print("Testing murder query...")
    resolver = StatuteResolver()
    result = resolver.resolve_query('i murdered my friend', ['criminal'], 'IN')
    print('Result:', result)

if __name__ == "__main__":
    test_murder_query()