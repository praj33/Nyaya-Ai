#!/usr/bin/env python3
"""Quick script to count all sections in database"""
import json
import os

total = 0
by_file = {}

for f in os.listdir('db'):
    if f.endswith('.json'):
        with open(os.path.join('db', f), 'r', encoding='utf-8') as file:
            data = json.load(file)
            count = 0
            
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
            elif 'criminal_law' in data or 'civil_law' in data:
                for law in ['criminal_law', 'civil_law']:
                    if law in data:
                        for act, secs in data[law].items():
                            count += len(secs) if isinstance(secs, dict) else 0
            
            if count > 0:
                by_file[f] = count
                total += count

print(f"TOTAL SECTIONS: {total}")
print(f"\nBreakdown by file:")
for f, c in sorted(by_file.items(), key=lambda x: x[1], reverse=True):
    print(f"  {f}: {c}")
