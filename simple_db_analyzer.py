#!/usr/bin/env python3
"""
Simple Database Analyzer
"""
import json
import os
from collections import defaultdict

def analyze_database():
    db_path = "db"
    total_sections = 0
    total_acts = set()
    files_data = {}
    jurisdiction_stats = defaultdict(lambda: {"sections": 0, "acts": set(), "files": []})
    
    print("Loading database files...")
    
    # Load all JSON files
    for filename in os.listdir(db_path):
        if filename.endswith('.json'):
            filepath = os.path.join(db_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    files_data[filename] = data
                    print(f"Loaded: {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    print(f"\n{'='*80}")
    print("DATABASE ANALYSIS REPORT")
    print(f"{'='*80}")
    
    # Analyze each file
    file_analyses = []
    for filename, data in files_data.items():
        analysis = {
            "filename": filename,
            "sections": 0,
            "acts": set(),
            "jurisdiction": "Unknown",
            "size_kb": round(len(json.dumps(data)) / 1024, 2)
        }
        
        # Detect jurisdiction
        if any(x in filename.lower() for x in ['india', 'ipc', 'crpc', 'bns']):
            analysis["jurisdiction"] = "IN"
        elif any(x in filename.lower() for x in ['uk', 'britain']):
            analysis["jurisdiction"] = "UK"
        elif any(x in filename.lower() for x in ['uae', 'emirates']):
            analysis["jurisdiction"] = "UAE"
        
        # Count sections and acts
        if isinstance(data, dict):
            if "sections" in data and isinstance(data["sections"], list):
                analysis["sections"] = len(data["sections"])
                for section in data["sections"]:
                    if isinstance(section, dict) and "act_id" in section:
                        analysis["acts"].add(section["act_id"])
            
            elif "acts" in data and isinstance(data["acts"], dict):
                for act_name, act_data in data["acts"].items():
                    analysis["acts"].add(act_name)
                    if isinstance(act_data, dict) and "sections" in act_data:
                        if isinstance(act_data["sections"], list):
                            analysis["sections"] += len(act_data["sections"])
            
            else:
                # Check for direct sections or act-based structure
                for key, value in data.items():
                    if isinstance(value, list):
                        analysis["sections"] += len(value)
                        analysis["acts"].add(key)
                    elif isinstance(value, dict) and "sections" in value:
                        if isinstance(value["sections"], list):
                            analysis["sections"] += len(value["sections"])
                            analysis["acts"].add(key)
        
        elif isinstance(data, list):
            analysis["sections"] = len(data)
            for item in data:
                if isinstance(item, dict) and "act_id" in item:
                    analysis["acts"].add(item["act_id"])
        
        file_analyses.append(analysis)
        
        # Update totals
        total_sections += analysis["sections"]
        total_acts.update(analysis["acts"])
        
        # Update jurisdiction stats
        jurisdiction = analysis["jurisdiction"]
        jurisdiction_stats[jurisdiction]["sections"] += analysis["sections"]
        jurisdiction_stats[jurisdiction]["acts"].update(analysis["acts"])
        jurisdiction_stats[jurisdiction]["files"].append(filename)
    
    # Print overall statistics
    print(f"\nOVERALL STATISTICS:")
    print(f"   Total Files: {len(files_data)}")
    print(f"   Total Sections: {total_sections:,}")
    print(f"   Total Acts: {len(total_acts)}")
    print(f"   Total Database Size: {sum(a['size_kb'] for a in file_analyses):.1f} KB")
    
    # Jurisdiction breakdown
    print(f"\nJURISDICTION BREAKDOWN:")
    for jurisdiction, stats in jurisdiction_stats.items():
        if stats["sections"] > 0:
            print(f"   {jurisdiction}:")
            print(f"      Sections: {stats['sections']:,}")
            print(f"      Acts: {len(stats['acts'])}")
            print(f"      Files: {len(stats['files'])}")
    
    # Top files by sections
    print(f"\nTOP 10 FILES BY SECTIONS:")
    top_files = sorted(file_analyses, key=lambda x: x["sections"], reverse=True)[:10]
    for i, analysis in enumerate(top_files, 1):
        print(f"   {i:2}. {analysis['filename']:<35} - {analysis['sections']:,} sections ({analysis['jurisdiction']})")
    
    # Detailed file analysis
    print(f"\nDETAILED FILE ANALYSIS:")
    print(f"{'Filename':<40} {'Jurisdiction':<12} {'Sections':<10} {'Acts':<6} {'Size(KB)'}")
    print("-" * 80)
    
    for analysis in sorted(file_analyses, key=lambda x: x["sections"], reverse=True):
        print(f"{analysis['filename']:<40} {analysis['jurisdiction']:<12} {analysis['sections']:<10} {len(analysis['acts']):<6} {analysis['size_kb']}")
    
    # Jurisdiction details
    print(f"\nJURISDICTION DETAILS:")
    for jurisdiction, stats in jurisdiction_stats.items():
        if stats["sections"] > 0:
            print(f"\n{jurisdiction} JURISDICTION:")
            print(f"   Total Sections: {stats['sections']:,}")
            print(f"   Total Acts: {len(stats['acts'])}")
            print(f"   Files:")
            for filename in sorted(stats['files']):
                file_analysis = next(a for a in file_analyses if a['filename'] == filename)
                print(f"      {filename:<35} - {file_analysis['sections']:,} sections")
            
            if len(stats['acts']) > 0:
                print(f"   Sample Acts:")
                for act in sorted(list(stats['acts']))[:15]:
                    print(f"      {act}")
                if len(stats['acts']) > 15:
                    print(f"      ... and {len(stats['acts']) - 15} more acts")
    
    print(f"\n{'='*80}")
    print(f"ANALYSIS COMPLETE!")
    print(f"Database contains {total_sections:,} sections across {len(total_acts)} acts in {len(files_data)} files")
    print(f"{'='*80}")

if __name__ == "__main__":
    analyze_database()