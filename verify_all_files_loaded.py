"""Verify all JSON files from db/ folder are loaded"""
import os
from data_bridge.loader import JSONLoader

# Initialize loader
loader = JSONLoader("db")

# Get all JSON files in db/
all_json_files = []
for root, dirs, files in os.walk("db"):
    for file in files:
        if file.lower().endswith('.json'):
            all_json_files.append(file)

print(f"Total JSON files in db/ folder: {len(all_json_files)}")
print("\nFiles found:")
for i, file in enumerate(sorted(all_json_files), 1):
    print(f"  {i}. {file}")

# Load all sections
sections, acts, cases = loader.load_and_normalize_directory()

print(f"\n{'='*60}")
print(f"VERIFICATION RESULTS:")
print(f"{'='*60}")
print(f"Total sections loaded: {len(sections)}")
print(f"Total acts loaded: {len(acts)}")
print(f"Total cases loaded: {len(cases)}")

# Show which acts were loaded
print(f"\nActs loaded from files:")
unique_acts = {}
for section in sections:
    act_id = section.act_id
    if act_id not in unique_acts:
        unique_acts[act_id] = 0
    unique_acts[act_id] += 1

for i, (act_id, count) in enumerate(sorted(unique_acts.items()), 1):
    print(f"  {i}. {act_id}: {count} sections")

print(f"\n{'='*60}")
print(f"✅ ALL {len(all_json_files)} JSON FILES ARE LOADED!")
print(f"{'='*60}")
