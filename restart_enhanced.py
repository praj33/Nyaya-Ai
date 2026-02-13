#!/usr/bin/env python3
"""
Restart Enhanced Backend
Forces reload of enhanced legal advisor
"""
import subprocess
import sys
import os
import time
import requests

def restart_backend():
    print("Restarting backend with enhanced legal advisor...")
    
    # Change to correct directory
    os.chdir(r"c:\Users\Gauri\Desktop\Nyaya-Ai\Nyaya_AI")
    
    # Set environment variables
    os.environ["HMAC_SECRET_KEY"] = "nyaya-ai-secret-key-2025"
    os.environ["PORT"] = "8000"
    
    print("Starting enhanced backend on port 8000...")
    print("Enhanced legal advisor integrated")
    print("Press Ctrl+C to stop")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\nServer stopped")

if __name__ == "__main__":
    restart_backend()