import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time

class SCIndiaScraper:
    def __init__(self):
        self.base_url = "https://main.sci.gov.in/judgments"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_recent_judgments(self, limit: int = 10) -> List[Dict]:
        judgments = []
        
        # Mock data for demonstration (actual scraping requires valid SSL and website structure)
        for i in range(min(limit, 5)):
            judgment = {
                'case_title': f'Sample Case {i+1} vs State',
                'court': 'Supreme Court of India',
                'year': 2025,
                'citation': f'2025 SCC {i+1}',
                'judgment_text': f'This is a sample judgment text for case {i+1}. The court held that...',
                'url': f'{self.base_url}/case-{i+1}'
            }
            judgments.append(judgment)
        
        return judgments
    
    def get_judgment_details(self, url: str) -> Dict:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return {
                'full_text': soup.get_text(strip=True)[:5000],
                'url': url
            }
        
        except Exception as e:
            print(f"Error fetching details: {e}")
            return {}
