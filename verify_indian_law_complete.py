"""Verify ALL data from indian_law_dataset.json is loaded"""
import json
from data_bridge.loader import JSONLoader

# Load the file directly to count what should be loaded
with open('db/indian_law_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 70)
print("INDIAN_LAW_DATASET.JSON CONTENT:")
print("=" * 70)

# Count what's in the file
bns_count = len(data.get('bns_sections', {}))
civil_count = len(data.get('civil_law', {}))
special_count = len(data.get('special_laws', {}))

print(f"\n1. BNS Sections (Criminal): {bns_count}")
print(f"2. Civil Law Sections: {civil_count}")
print(f"3. Special Laws: {special_count}")
print(f"\nTOTAL in file: {bns_count + civil_count + special_count}")

# Now check what's loaded
loader = JSONLoader("db")
sections, acts, cases = loader.load_and_normalize_directory()

# Find sections from indian_law_dataset.json
indian_law_sections = [s for s in sections if 'indian_law_dataset' in s.act_id]

print("\n" + "=" * 70)
print("LOADED FROM INDIAN_LAW_DATASET.JSON:")
print("=" * 70)

bns_loaded = [s for s in indian_law_sections if 'bns' in s.act_id]
civil_loaded = [s for s in indian_law_sections if 'civil' in s.act_id]
special_loaded = [s for s in indian_law_sections if 'special' in s.act_id]

print(f"\n1. BNS Sections loaded: {len(bns_loaded)}")
print(f"2. Civil Law sections loaded: {len(civil_loaded)}")
print(f"3. Special Laws loaded: {len(special_loaded)}")
print(f"\nTOTAL loaded: {len(indian_law_sections)}")

# Verify completeness
print("\n" + "=" * 70)
print("VERIFICATION:")
print("=" * 70)
if bns_count == len(bns_loaded):
    print(f"[SUCCESS] BNS Sections: ALL {bns_count} loaded")
else:
    print(f"[FAIL] BNS Sections: {len(bns_loaded)}/{bns_count} loaded (MISSING {bns_count - len(bns_loaded)})")

if civil_count == len(civil_loaded):
    print(f"[SUCCESS] Civil Law: ALL {civil_count} loaded")
else:
    print(f"[FAIL] Civil Law: {len(civil_loaded)}/{civil_count} loaded (MISSING {civil_count - len(civil_loaded)})")

if special_count == len(special_loaded):
    print(f"[SUCCESS] Special Laws: ALL {special_count} loaded")
else:
    print(f"[FAIL] Special Laws: {len(special_loaded)}/{special_count} loaded (MISSING {special_count - len(special_loaded)})")

total_expected = bns_count + civil_count + special_count
total_loaded = len(indian_law_sections)

print(f"\n{'='*70}")
if total_expected == total_loaded:
    print(f"[SUCCESS] ALL {total_expected} sections from indian_law_dataset.json are loaded!")
else:
    print(f"[FAIL] INCOMPLETE: {total_loaded}/{total_expected} loaded (MISSING {total_expected - total_loaded})")
print(f"{'='*70}")
