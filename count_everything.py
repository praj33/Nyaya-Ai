#!/usr/bin/env python3
import json
import os

def count_sections_in_file(data):
    """Count sections in various JSON structures"""
    count = 0
    
    if isinstance(data, dict):
        if 'key_sections' in data:
            for cat, secs in data['key_sections'].items():
                count += len(secs) if isinstance(secs, dict) else 0
        elif 'bns_sections' in data:
            count = len(data['bns_sections']) if isinstance(data['bns_sections'], dict) else 0
        elif 'key_provisions' in data:
            if isinstance(data['key_provisions'], dict):
                for cat, provs in data['key_provisions'].items():
                    count += len(provs) if isinstance(provs, dict) else 0
        elif 'sections' in data:
            count = len(data['sections']) if isinstance(data['sections'], (dict, list)) else 0
        elif 'structure' in data:
            for part, content in data['structure'].items():
                if isinstance(content, dict):
                    count += len(content)
        elif 'criminal_law' in data or 'civil_law' in data:
            for law in ['criminal_law', 'civil_law']:
                if law in data and isinstance(data[law], dict):
                    for act, secs in data[law].items():
                        count += len(secs) if isinstance(secs, dict) else 0
    
    return count

# Count main database
print("=" * 60)
print("COUNTING ALL LEGAL SECTIONS")
print("=" * 60)

main_db_total = 0
main_db_files = {}

db_path = 'db'
for f in os.listdir(db_path):
    if f.endswith('.json'):
        try:
            with open(os.path.join(db_path, f), 'r', encoding='utf-8') as file:
                data = json.load(file)
                count = count_sections_in_file(data)
                if count > 0:
                    main_db_files[f] = count
                    main_db_total += count
        except Exception as e:
            print(f"Error in {f}: {e}")

print(f"\n1. MAIN DATABASE (Nyaya_AI/db/):")
print(f"   Total Files: {len(main_db_files)}")
print(f"   Total Sections: {main_db_total}")
print(f"\n   Top 10 files:")
for f, c in sorted(main_db_files.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"     {f}: {c}")

# Count procedure datasets
proc_total = 0
proc_by_jurisdiction = {}

proc_base = '../nyaya-legal-procedure-datasets/data/procedures'
if os.path.exists(proc_base):
    for jurisdiction in os.listdir(proc_base):
        juris_path = os.path.join(proc_base, jurisdiction)
        if os.path.isdir(juris_path):
            proc_by_jurisdiction[jurisdiction] = 0
            for domain_file in os.listdir(juris_path):
                if domain_file.endswith('.json'):
                    try:
                        with open(os.path.join(juris_path, domain_file), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            count = count_sections_in_file(data)
                            proc_by_jurisdiction[jurisdiction] += count
                            proc_total += count
                    except Exception as e:
                        pass

print(f"\n2. PROCEDURE DATASETS (nyaya-legal-procedure-datasets/):")
print(f"   Total Jurisdictions: {len(proc_by_jurisdiction)}")
print(f"   Total Procedure Sections: {proc_total}")
for juris, count in proc_by_jurisdiction.items():
    print(f"     {juris}: {count}")

# Grand total
grand_total = main_db_total + proc_total
print(f"\n" + "=" * 60)
print(f"GRAND TOTAL: {grand_total} sections")
print(f"  - Main Database: {main_db_total}")
print(f"  - Procedure Datasets: {proc_total}")
print("=" * 60)
