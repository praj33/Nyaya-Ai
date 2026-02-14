import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from data_bridge.loader import JSONLoader

def verify_db_loading():
    print("=" * 80)
    print("VERIFYING DATABASE LOADING FROM db/ FOLDER")
    print("=" * 80)
    
    loader = JSONLoader("db")
    sections, acts, cases = loader.load_and_normalize_directory()
    
    print(f"\nTotal sections loaded: {len(sections)}")
    print(f"Total acts loaded: {len(acts)}")
    print(f"Total cases loaded: {len(cases)}")
    
    # Check for BNS sections
    bns_sections = [s for s in sections if 'bharatiya' in s.act_id.lower() or 'bns' in s.act_id.lower()]
    print(f"\n[BNS] Bharatiya Nyaya Sanhita sections: {len(bns_sections)}")
    if bns_sections:
        print(f"  Sample sections: {[s.section_number for s in bns_sections[:5]]}")
        print(f"  Sample act_id: {bns_sections[0].act_id}")
    
    # Check for IPC sections
    ipc_sections = [s for s in sections if 'ipc' in s.act_id.lower() or 'indian_penal' in s.act_id.lower() or 'penal_code' in s.act_id.lower()]
    print(f"\n[IPC] Indian Penal Code sections: {len(ipc_sections)}")
    if ipc_sections:
        print(f"  Sample sections: {[s.section_number for s in ipc_sections[:5]]}")
        print(f"  Sample act_id: {ipc_sections[0].act_id}")
    
    # Check for CrPC sections
    crpc_sections = [s for s in sections if 'crpc' in s.act_id.lower() or 'criminal_procedure' in s.act_id.lower()]
    print(f"\n[CrPC] Criminal Procedure Code sections: {len(crpc_sections)}")
    if crpc_sections:
        print(f"  Sample sections: {[s.section_number for s in crpc_sections[:5]]}")
        print(f"  Sample act_id: {crpc_sections[0].act_id}")
    
    # List all unique act_ids
    unique_acts = set(s.act_id for s in sections)
    print(f"\n[ALL ACTS] Total unique acts: {len(unique_acts)}")
    print("\nAct IDs loaded:")
    for act_id in sorted(unique_acts):
        count = len([s for s in sections if s.act_id == act_id])
        print(f"  - {act_id}: {count} sections")
    
    # Check specific files in db folder
    print("\n" + "=" * 80)
    print("CHECKING db/ FOLDER FILES")
    print("=" * 80)
    
    db_path = os.path.join(os.path.dirname(__file__), "..", "db")
    if os.path.exists(db_path):
        files = [f for f in os.listdir(db_path) if f.endswith('.json')]
        print(f"\nJSON files in db/ folder: {len(files)}")
        
        # Check for specific files
        target_files = ['bns_sections.json', 'ipc_sections.json', 'crpc_sections.json']
        for target in target_files:
            if target in files:
                file_path = os.path.join(db_path, target)
                file_size = os.path.getsize(file_path)
                print(f"  [FOUND] {target} ({file_size:,} bytes)")
            else:
                print(f"  [MISSING] {target}")
    else:
        print(f"\n[ERROR] db/ folder not found at: {db_path}")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    
    # Summary
    if bns_sections or ipc_sections or crpc_sections:
        print("\n[SUCCESS] System is loading sections from db/ folder")
        print(f"  - BNS: {len(bns_sections)} sections")
        print(f"  - IPC: {len(ipc_sections)} sections")
        print(f"  - CrPC: {len(crpc_sections)} sections")
    else:
        print("\n[WARNING] No BNS/IPC/CrPC sections found")

if __name__ == "__main__":
    verify_db_loading()
