#!/usr/bin/env python3
"""
Enhanced Backend Testing Script
Tests the enhanced legal advisor system through the API
"""
import requests
import json
import time
from typing import Dict, Any

class EnhancedBackendTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self) -> bool:
        """Test if backend is running"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    def test_enhanced_queries(self):
        """Test enhanced legal advisor with comprehensive queries"""
        test_queries = [
            {
                "query": "What is the punishment for rape in India?",
                "expected_sections": ["375", "376"],
                "jurisdiction": "India"
            },
            {
                "query": "Theft penalties under UK law",
                "expected_sections": ["theft"],
                "jurisdiction": "UK"
            },
            {
                "query": "UAE commercial law violations",
                "expected_sections": ["commercial"],
                "jurisdiction": "UAE"
            },
            {
                "query": "Murder charges in Indian Penal Code",
                "expected_sections": ["302", "300"],
                "jurisdiction": "India"
            },
            {
                "query": "What are the procedures for filing a case in Mumbai court?",
                "expected_sections": ["procedure"],
                "jurisdiction": "India"
            }
        ]
        
        results = []
        for i, test in enumerate(test_queries, 1):
            print(f"\n=== Test {i}: {test['query']} ===")
            
            try:
                # Test main query endpoint
                response = self.session.post(
                    f"{self.base_url}/nyaya/query",
                    json={"query": test["query"]}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Status: SUCCESS")
                    print(f"📊 Confidence: {data.get('confidence', 'N/A')}")
                    print(f"🏛️ Jurisdiction: {data.get('jurisdiction', 'N/A')}")
                    print(f"📚 Sections Found: {len(data.get('relevant_sections', []))}")
                    
                    # Show first few sections
                    sections = data.get('relevant_sections', [])[:3]
                    for section in sections:
                        print(f"   - Section {section.get('section_number', 'N/A')}: {section.get('text', 'N/A')[:100]}...")
                    
                    results.append({
                        "query": test["query"],
                        "status": "SUCCESS",
                        "confidence": data.get('confidence'),
                        "sections_count": len(data.get('relevant_sections', [])),
                        "jurisdiction": data.get('jurisdiction')
                    })
                else:
                    print(f"❌ Status: FAILED ({response.status_code})")
                    print(f"Error: {response.text}")
                    results.append({
                        "query": test["query"],
                        "status": "FAILED",
                        "error": response.text
                    })
                    
            except Exception as e:
                print(f"❌ Status: ERROR - {str(e)}")
                results.append({
                    "query": test["query"],
                    "status": "ERROR",
                    "error": str(e)
                })
            
            time.sleep(1)  # Rate limiting
        
        return results
    
    def test_multi_jurisdiction(self):
        """Test multi-jurisdiction endpoint"""
        print(f"\n=== Multi-Jurisdiction Test ===")
        
        try:
            response = self.session.post(
                f"{self.base_url}/nyaya/multi_jurisdiction",
                json={
                    "query": "What are the penalties for fraud?",
                    "jurisdictions": ["IN", "UK", "UAE"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Multi-jurisdiction query successful")
                for jurisdiction, result in data.get('results', {}).items():
                    print(f"   {jurisdiction}: {len(result.get('relevant_sections', []))} sections")
                return True
            else:
                print(f"❌ Multi-jurisdiction failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Multi-jurisdiction error: {str(e)}")
            return False
    
    def generate_report(self, results: list):
        """Generate test report"""
        print(f"\n{'='*60}")
        print(f"ENHANCED BACKEND TEST REPORT")
        print(f"{'='*60}")
        
        total_tests = len(results)
        successful_tests = len([r for r in results if r['status'] == 'SUCCESS'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        print(f"\nDetailed Results:")
        for result in results:
            status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
            print(f"{status_icon} {result['query'][:50]}...")
            if result['status'] == 'SUCCESS':
                print(f"   Confidence: {result.get('confidence', 'N/A')}")
                print(f"   Sections: {result.get('sections_count', 0)}")
                print(f"   Jurisdiction: {result.get('jurisdiction', 'N/A')}")

def main():
    print("🚀 Starting Enhanced Backend Testing...")
    
    tester = EnhancedBackendTester()
    
    # Check if backend is running
    print("🔍 Checking backend health...")
    if not tester.test_health():
        print("❌ Backend is not running!")
        print("Please start the backend first:")
        print("   cd c:\\Users\\Gauri\\Desktop\\Nyaya-Ai\\Nyaya_AI")
        print("   start_backend.bat")
        return
    
    print("✅ Backend is running!")
    
    # Run comprehensive tests
    results = tester.test_enhanced_queries()
    
    # Test multi-jurisdiction
    tester.test_multi_jurisdiction()
    
    # Generate report
    tester.generate_report(results)
    
    print(f"\n🎯 Testing complete! Check the results above.")
    print(f"📊 API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()