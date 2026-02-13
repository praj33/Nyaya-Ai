#!/usr/bin/env python3
"""
Nyaya AI System Quick Start
Simple startup script for the complete system
"""

import os
import sys

def main():
    print("=== NYAYA AI SYSTEM STARTUP ===")
    
    # Check if we're in the right directory
    if not os.path.exists('Nyaya_AI'):
        print("Error: Run this from the Nyaya-Ai root directory")
        print("Current directory:", os.getcwd())
        return
    
    # Check key files
    key_files = [
        'Nyaya_AI/integrated_legal_advisor.py',
        'Nyaya_AI/enforcement_ledger.json',
        'Nyaya_AI/data_bridge/loader.py'
    ]
    
    missing = [f for f in key_files if not os.path.exists(f)]
    if missing:
        print("Missing files:", missing)
        return
    
    print("All key files found. System ready!")
    print("\nStartup options:")
    print("1. Run integrated legal advisor")
    print("2. Test system components")
    print("3. Show system status")
    
    choice = input("\nSelect (1-3): ").strip()
    
    if choice == "1":
        print("\nStarting integrated legal advisor...")
        os.system(f"{sys.executable} Nyaya_AI/integrated_legal_advisor.py")
    
    elif choice == "2":
        print("\nTesting components...")
        test_system()
    
    elif choice == "3":
        show_status()
    
    else:
        print("Invalid choice")

def test_system():
    """Test system components"""
    print("Testing Data Bridge...")
    try:
        import sys
        sys.path.append('Nyaya_AI')
        from data_bridge.loader import DataBridge
        db = DataBridge()
        print("  Data Bridge: OK")
    except Exception as e:
        print(f"  Data Bridge: ERROR - {e}")
    
    print("Testing Enforcement Ledger...")
    try:
        import json
        with open('Nyaya_AI/enforcement_ledger.json') as f:
            data = json.load(f)
        print(f"  Enforcement Ledger: OK ({len(data)} entries)")
    except Exception as e:
        print(f"  Enforcement Ledger: ERROR - {e}")

def show_status():
    """Show system status"""
    print("\n=== SYSTEM STATUS ===")
    
    components = {
        "Data Bridge": "Nyaya_AI/data_bridge/loader.py",
        "Enforcement Ledger": "Nyaya_AI/enforcement_ledger.json",
        "Legal Database": "Nyaya_AI/db/",
        "Integrated Advisor": "Nyaya_AI/integrated_legal_advisor.py"
    }
    
    for name, path in components.items():
        status = "READY" if os.path.exists(path) else "MISSING"
        print(f"  {name}: {status}")
    
    if os.path.exists("Nyaya_AI/db/"):
        db_files = len([f for f in os.listdir("Nyaya_AI/db/") if f.endswith('.json')])
        print(f"  Database Files: {db_files}")
    
    print(f"\nQuick start command:")
    print(f"  python Nyaya_AI/integrated_legal_advisor.py")

if __name__ == "__main__":
    main()