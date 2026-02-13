import json
import os
import time
from pathlib import Path
from core.scrapers.sc_india_scraper import SCIndiaScraper
from core.scrapers.caselaw_parser import CaselawParser

class CaselawScheduler:
    def __init__(self, output_dir="data/caselaw_scraped"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.scraper = SCIndiaScraper()
        self.parser = CaselawParser()
    
    def run_once(self, limit: int = 10):
        print(f"Starting scrape at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        raw_judgments = self.scraper.scrape_recent_judgments(limit=limit)
        
        saved_count = 0
        skipped_count = 0
        
        for raw in raw_judgments:
            parsed = self.parser.parse(raw)
            case_id = self.parser.generate_case_id(parsed)
            
            file_path = self.output_dir / f"{case_id}.json"
            
            if file_path.exists():
                skipped_count += 1
                continue
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)
            
            saved_count += 1
        
        print(f"Saved: {saved_count}, Skipped: {skipped_count}")
        return saved_count, skipped_count
    
    def run_daily(self):
        while True:
            self.run_once()
            time.sleep(86400)
