import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ontology.statute_resolver import StatuteResolver

def debug_authority_assault():
    resolver = StatuteResolver()
    
    query = "my teacher is beating me"
    print(f"Query: {query}")
    
    subtype = resolver.detect_offense_subtype(query)
    print(f"Detected subtype: {subtype}")
    
    # Check offense subtypes data
    print(f"Available subtypes: {list(resolver.offense_subtypes.keys())}")
    
    if "authority_assault" in resolver.offense_subtypes:
        authority_data = resolver.offense_subtypes["authority_assault"]
        print(f"Authority assault data: {authority_data}")
        
        query_lower = query.lower()
        keywords = authority_data.get('keywords', [])
        trigger_verbs = authority_data.get('trigger_verbs', [])
        
        print(f"Keywords: {keywords}")
        print(f"Trigger verbs: {trigger_verbs}")
        
        has_authority = any(kw in query_lower for kw in keywords)
        has_violence = any(verb in query_lower for verb in trigger_verbs)
        
        print(f"Has authority keyword: {has_authority}")
        print(f"Has violence verb: {has_violence}")
        print(f"Should match: {has_authority and has_violence}")

if __name__ == "__main__":
    debug_authority_assault()