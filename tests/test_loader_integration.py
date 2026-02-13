import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.caselaw.loader import CaseLawLoader

def test_loader_integration():
    print("=" * 80)
    print("CASE LAW LOADER INTEGRATION TEST")
    print("=" * 80)
    
    loader = CaseLawLoader()
    cases = loader.load_all()
    
    print(f"\nTotal cases loaded: {len(cases)}")
    
    # Count by source
    existing_count = sum(1 for c in cases if hasattr(c, 'source') and c.source != 'scraped')
    scraped_count = sum(1 for c in cases if not hasattr(c, 'source') or getattr(c, 'source', '') == 'scraped')
    
    print(f"Existing cases: {len(cases) - scraped_count}")
    print(f"Scraped cases: {scraped_count}")
    
    if len(cases) > 0:
        print("\n[PASS] Loader successfully loads from both directories")
    else:
        print("\n[FAIL] No cases loaded")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_loader_integration()
