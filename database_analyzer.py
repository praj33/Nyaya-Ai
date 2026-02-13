#!/usr/bin/env python3
"""
Comprehensive Database Analyzer
Analyzes all JSON files in the database to provide detailed statistics
"""
import json
import os
from collections import defaultdict, Counter
from typing import Dict, List, Any

class DatabaseAnalyzer:
    def __init__(self, db_path: str = "db"):
        self.db_path = db_path
        self.files_data = {}
        self.total_sections = 0
        self.total_acts = 0
        self.jurisdiction_stats = defaultdict(lambda: {"sections": 0, "acts": set(), "files": []})
        
    def load_all_files(self):
        """Load and analyze all JSON files"""
        print("Loading all database files...")
        
        for filename in os.listdir(self.db_path):
            if filename.endswith('.json'):
                filepath = os.path.join(self.db_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.files_data[filename] = data
                        print(f"Loaded: {filename}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
    
    def analyze_file_structure(self, filename: str, data: Any) -> Dict[str, Any]:
        """Analyze structure of a single file"""
        analysis = {
            "filename": filename,
            "type": type(data).__name__,
            "size_kb": round(len(json.dumps(data)) / 1024, 2),
            "sections": 0,
            "acts": set(),
            "jurisdiction": "Unknown",
            "structure": "Unknown"
        }
        
        # Detect jurisdiction from filename
        if any(x in filename.lower() for x in ['india', 'ipc', 'crpc', 'bns']):
            analysis["jurisdiction"] = "IN"
        elif any(x in filename.lower() for x in ['uk', 'britain', 'english']):
            analysis["jurisdiction"] = "UK"
        elif any(x in filename.lower() for x in ['uae', 'emirates']):
            analysis["jurisdiction"] = "UAE"
        
        if isinstance(data, dict):
            # Check for different structures
            if "sections" in data:
                analysis["structure"] = "sections_dict"
                sections = data["sections"]
                if isinstance(sections, list):
                    analysis["sections"] = len(sections)
                    for section in sections:
                        if isinstance(section, dict) and "act_id" in section:
                            analysis["acts"].add(section["act_id"])
                elif isinstance(sections, dict):
                    analysis["sections"] = len(sections)
                    analysis["acts"].update(sections.keys())
            
            elif any(key.endswith("_sections") for key in data.keys()):
                analysis["structure"] = "act_sections_dict"
                for key, value in data.items():
                    if key.endswith("_sections") and isinstance(value, list):
                        analysis["sections"] += len(value)
                        analysis["acts"].add(key.replace("_sections", ""))
            
            elif "acts" in data:
                analysis["structure"] = "acts_dict"
                acts = data["acts"]
                if isinstance(acts, dict):
                    for act_name, act_data in acts.items():
                        analysis["acts"].add(act_name)
                        if isinstance(act_data, dict) and "sections" in act_data:
                            if isinstance(act_data["sections"], list):
                                analysis["sections"] += len(act_data["sections"])
            
            else:
                # Direct sections in root
                analysis["structure"] = "direct_sections"
                for key, value in data.items():
                    if isinstance(value, list):
                        analysis["sections"] += len(value)
                        analysis["acts"].add(key)
                    elif isinstance(value, dict) and "sections" in value:
                        if isinstance(value["sections"], list):
                            analysis["sections"] += len(value["sections"])
                            analysis["acts"].add(key)
        
        elif isinstance(data, list):
            analysis["structure"] = "sections_list"
            analysis["sections"] = len(data)
            for item in data:
                if isinstance(item, dict) and "act_id" in item:
                    analysis["acts"].add(item["act_id"])
        
        return analysis
    
    def generate_comprehensive_report(self):
        """Generate detailed analysis report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE DATABASE ANALYSIS REPORT")
        print("="*80)
        
        file_analyses = []
        total_sections = 0
        total_acts = set()
        jurisdiction_breakdown = defaultdict(lambda: {"sections": 0, "acts": set(), "files": []})
        
        # Analyze each file
        for filename, data in self.files_data.items():
            analysis = self.analyze_file_structure(filename, data)
            file_analyses.append(analysis)
            
            total_sections += analysis["sections"]
            total_acts.update(analysis["acts"])
            
            jurisdiction = analysis["jurisdiction"]
            jurisdiction_breakdown[jurisdiction]["sections"] += analysis["sections"]
            jurisdiction_breakdown[jurisdiction]["acts"].update(analysis["acts"])
            jurisdiction_breakdown[jurisdiction]["files"].append(filename)
        
        # Overall Statistics
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total Files: {len(self.files_data)}")
        print(f"   Total Sections: {total_sections:,}")
        print(f"   Total Acts: {len(total_acts)}")
        print(f"   Total Database Size: {sum(a['size_kb'] for a in file_analyses):.1f} KB")
        
        # Jurisdiction Breakdown
        print(f"\n🏛️ JURISDICTION BREAKDOWN:")
        for jurisdiction, stats in jurisdiction_breakdown.items():
            print(f"   {jurisdiction}:")
            print(f"      Sections: {stats['sections']:,}")
            print(f"      Acts: {len(stats['acts'])}")
            print(f"      Files: {len(stats['files'])}")
        
        # File-by-File Analysis
        print(f"\n📁 FILE-BY-FILE ANALYSIS:")
        print(f"{'Filename':<35} {'Jurisdiction':<12} {'Sections':<10} {'Acts':<6} {'Size(KB)':<10} {'Structure'}")
        print("-" * 90)
        
        for analysis in sorted(file_analyses, key=lambda x: x["sections"], reverse=True):
            print(f"{analysis['filename']:<35} {analysis['jurisdiction']:<12} {analysis['sections']:<10} {len(analysis['acts']):<6} {analysis['size_kb']:<10} {analysis['structure']}")
        
        # Top Files by Sections
        print(f"\n🔝 TOP 10 FILES BY SECTIONS:")
        top_files = sorted(file_analyses, key=lambda x: x["sections"], reverse=True)[:10]
        for i, analysis in enumerate(top_files, 1):
            print(f"   {i:2}. {analysis['filename']:<30} - {analysis['sections']:,} sections")
        
        # Structure Types
        print(f"\n🏗️ FILE STRUCTURE TYPES:")
        structure_counts = Counter(a["structure"] for a in file_analyses)
        for structure, count in structure_counts.items():
            print(f"   {structure:<20}: {count} files")
        
        # Detailed Jurisdiction Analysis
        print(f"\n🔍 DETAILED JURISDICTION ANALYSIS:")
        for jurisdiction, stats in jurisdiction_breakdown.items():
            if stats["sections"] > 0:
                print(f"\n   {jurisdiction} JURISDICTION:")
                print(f"      Total Sections: {stats['sections']:,}")
                print(f"      Total Acts: {len(stats['acts'])}")
                print(f"      Files ({len(stats['files'])}):")
                for filename in sorted(stats['files']):
                    file_analysis = next(a for a in file_analyses if a['filename'] == filename)
                    print(f"         • {filename:<30} - {file_analysis['sections']:,} sections, {len(file_analysis['acts'])} acts")
                
                if len(stats['acts']) > 0:
                    print(f"      Sample Acts:")
                    for act in sorted(list(stats['acts']))[:10]:
                        print(f"         • {act}")
                    if len(stats['acts']) > 10:
                        print(f"         ... and {len(stats['acts']) - 10} more acts")
        
        # Data Quality Check
        print(f"\n✅ DATA QUALITY CHECK:")
        empty_files = [a for a in file_analyses if a["sections"] == 0]
        if empty_files:
            print(f"   Warning: Files with no sections ({len(empty_files)}):")
            for analysis in empty_files:
                print(f"      • {analysis['filename']}")
        else:
            print(f"   All files contain sections")
        
        large_files = [a for a in file_analyses if a["size_kb"] > 100]
        if large_files:
            print(f"   Large files (>100KB): {len(large_files)}")
            for analysis in large_files:
                print(f"      • {analysis['filename']}: {analysis['size_kb']} KB")
        
        return {
            "total_sections": total_sections,
            "total_acts": len(total_acts),
            "total_files": len(self.files_data),
            "jurisdiction_breakdown": dict(jurisdiction_breakdown),
            "file_analyses": file_analyses
        }

def main():
    analyzer = DatabaseAnalyzer()
    analyzer.load_all_files()
    
    if not analyzer.files_data:
        print("No JSON files found in db/ directory")
        return
    
    report = analyzer.generate_comprehensive_report()
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE!")
    print(f"Your database contains {report['total_sections']:,} sections across {report['total_acts']} acts in {report['total_files']} files.")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()