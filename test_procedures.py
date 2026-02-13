#!/usr/bin/env python3
"""
Quick test script to check procedures endpoints directly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_procedures_list():
    """Test the procedures list endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/nyaya/procedures/list")
        print(f"Procedures List Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error testing procedures list: {e}")
        return None

def test_procedure_summary(country="india", domain="criminal"):
    """Test the procedure summary endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/nyaya/procedures/summary/{country}/{domain}")
        print(f"Procedure Summary Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error testing procedure summary: {e}")
        return None

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error testing health: {e}")
        return None

if __name__ == "__main__":
    print("=== Testing Nyaya AI Endpoints ===")
    
    print("\n1. Testing Health Endpoint:")
    test_health()
    
    print("\n2. Testing Procedures List:")
    test_procedures_list()
    
    print("\n3. Testing Procedure Summary (india/criminal):")
    test_procedure_summary("india", "criminal")
    
    print("\n4. Testing Procedure Summary (India/criminal) - uppercase:")
    test_procedure_summary("India", "criminal")