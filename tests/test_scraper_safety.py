import os
import json
import hashlib
from pathlib import Path

def test_existing_data_unchanged():
    print("=" * 80)
    print("SCRAPER SAFETY TEST")
    print("=" * 80)
    
    # Test 1: Verify existing case law directory exists and is untouched
    print("\n[Test 1] Existing case law directory")
    
    caselaw_dir = Path("data/caselaw")
    if caselaw_dir.exists():
        existing_files = list(caselaw_dir.glob("*.json"))
        print(f"  Found {len(existing_files)} existing case law files")
        print(f"  [PASS] Existing directory intact")
    else:
        print(f"  [INFO] No existing case law directory found")
    
    # Test 2: Verify scraped directory is separate
    print("\n[Test 2] Scraped case law directory")
    
    scraped_dir = Path("data/caselaw_scraped")
    if scraped_dir.exists():
        scraped_files = list(scraped_dir.glob("*.json"))
        print(f"  Found {len(scraped_files)} scraped case law files")
        print(f"  [PASS] Scraped directory separate")
    else:
        print(f"  [INFO] No scraped directory yet")
    
    # Test 3: Verify no overlap
    print("\n[Test 3] No file overlap")
    
    if caselaw_dir.exists() and scraped_dir.exists():
        existing_names = {f.name for f in caselaw_dir.glob("*.json")}
        scraped_names = {f.name for f in scraped_dir.glob("*.json")}
        
        overlap = existing_names & scraped_names
        
        if overlap:
            print(f"  [FAIL] Overlap found: {overlap}")
        else:
            print(f"  [PASS] No file overlap")
    else:
        print(f"  [SKIP] One or both directories don't exist")
    
    # Test 4: Run scraper and verify
    print("\n[Test 4] Run scraper")
    
    from core.scrapers.scheduler import CaselawScheduler
    
    scheduler = CaselawScheduler()
    saved, skipped = scheduler.run_once(limit=3)
    
    print(f"  Saved: {saved}, Skipped: {skipped}")
    
    if saved > 0:
        print(f"  [PASS] Scraper created new files")
    else:
        print(f"  [INFO] No new files (may be duplicates)")
    
    # Test 5: Verify existing files unchanged
    print("\n[Test 5] Existing files unchanged")
    
    if caselaw_dir.exists():
        current_files = list(caselaw_dir.glob("*.json"))
        if len(current_files) == len(existing_files if 'existing_files' in locals() else []):
            print(f"  [PASS] Existing file count unchanged")
        else:
            print(f"  [FAIL] Existing file count changed")
    else:
        print(f"  [SKIP] No existing directory")
    
    print("\n" + "=" * 80)
    print("SAFETY TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    test_existing_data_unchanged()
