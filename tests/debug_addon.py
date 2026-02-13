import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.addons.addon_subtype_resolver import AddonSubtypeResolver

def debug_addon_detection():
    resolver = AddonSubtypeResolver()
    
    queries = [
        "someone is cyber bullying me",
        "my boss touched me in office", 
        "seniors are ragging me in hostel"
    ]
    
    for query in queries:
        result = resolver.detect_addon_subtype(query)
        print(f"Query: '{query}' -> Result: {result}")
        
        # Check each subtype manually
        for subtype, data in resolver.addon_subtypes.items():
            keywords = data.get('keywords', [])
            matches = [kw for kw in keywords if kw in query.lower()]
            if matches:
                print(f"  {subtype}: matched keywords {matches}")

if __name__ == "__main__":
    debug_addon_detection()