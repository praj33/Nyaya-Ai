#!/usr/bin/env python3
"""
Enhanced Backend Startup Script
Starts the backend with enhanced legal advisor integration
"""
import os
import sys
import subprocess
import time
import requests

def check_backend_running(port=8000):
    """Check if backend is already running"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_backend():
    """Start the enhanced backend"""
    print("🚀 Starting Enhanced Nyaya AI Backend...")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir(r"c:\Users\Gauri\Desktop\Nyaya-Ai\Nyaya_AI")
    
    # Check if already running
    if check_backend_running():
        print("✅ Backend is already running!")
        print("📊 API Documentation: http://localhost:8000/docs")
        print("🔍 Health Check: http://localhost:8000/health")
        return
    
    # Set environment variables
    os.environ["HMAC_SECRET_KEY"] = "nyaya-ai-secret-key-2025-production-change-this-in-production"
    os.environ["PORT"] = "8000"
    os.environ["HOST"] = "0.0.0.0"
    
    print("🔧 Environment configured")
    print("🌐 Starting server on http://localhost:8000")
    print("📚 Enhanced legal advisor integrated")
    print("🏛️ Multi-jurisdiction support enabled")
    print()
    print("Available endpoints:")
    print("  - API Docs: http://localhost:8000/docs")
    print("  - Health: http://localhost:8000/health")
    print("  - Query: POST /nyaya/query")
    print("  - Multi-jurisdiction: POST /nyaya/multi_jurisdiction")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the server
        subprocess.run([
            "python", "-m", "uvicorn", 
            "api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    start_backend()