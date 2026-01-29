"""
Learning Memory Persistence for RL Engine
Stores aggregate learning data indexed by country, domain, and procedure_id
"""
import json
import sqlite3
import os
from datetime import datetime
from typing import Dict, Optional, Tuple


class LearningStore:
    def __init__(self, db_path: str = "performance_memory.json"):
        self.db_path = db_path
        self.data = self._load_data()
        self._initialize_structure()
    
    def _load_data(self) -> Dict:
        """Load learning data from persistent storage"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_data(self):
        """Save learning data to persistent storage"""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError:
            # Silently fail if unable to write
            pass
    
    def _initialize_structure(self):
        """Initialize the data structure if empty"""
        if 'learning_records' not in self.data:
            self.data['learning_records'] = {}
        if 'aggregates' not in self.data:
            self.data['aggregates'] = {}
    
    def store_signal(self, signal: Dict) -> None:
        """Store a learning signal in the persistent store"""
        country = signal.get('country', 'unknown')
        domain = signal.get('domain', 'unknown')
        procedure_id = signal.get('procedure_id', 'unknown')
        
        # Create unique key for this combination
        key = f"{country}:{domain}:{procedure_id}"
        
        if key not in self.data['learning_records']:
            self.data['learning_records'][key] = {
                'country': country,
                'domain': domain,
                'procedure_id': procedure_id,
                'aggregate_confidence_delta': 0.0,
                'success_count': 0,
                'failure_count': 0,
                'stability_factor': 1.0,
                'last_updated': None,
                'history': []
            }
        
        # Update the record
        record = self.data['learning_records'][key]
        record['last_updated'] = datetime.utcnow().isoformat()
        
        # Track success/failure based on outcome and feedback
        if signal.get('outcome_tag') == 'wrong' or signal.get('user_feedback') == 'negative':
            record['failure_count'] += 1
        elif signal.get('outcome_tag') == 'resolved' or signal.get('user_feedback') == 'positive':
            record['success_count'] += 1
        
        # Add to history
        record['history'].append({
            'case_id': signal.get('case_id'),
            'confidence_before': signal.get('confidence_before'),
            'user_feedback': signal.get('user_feedback'),
            'outcome_tag': signal.get('outcome_tag'),
            'timestamp': signal.get('timestamp')
        })
        
        # Keep history to a reasonable size
        if len(record['history']) > 100:
            record['history'] = record['history'][-50:]
        
        # Update stability factor based on success ratio
        total = record['success_count'] + record['failure_count']
        if total > 0:
            success_ratio = record['success_count'] / total
            # Stability increases with more data and consistent success
            record['stability_factor'] = min(1.0, 0.1 + (success_ratio * 0.9))
        
        self._save_data()
    
    def get_adjustment_for_context(self, country: str, domain: str, procedure_id: str) -> Tuple[float, float]:
        """Get the learned adjustment for a specific context"""
        key = f"{country}:{domain}:{procedure_id}"
        
        if key in self.data['learning_records']:
            record = self.data['learning_records'][key]
            return record['aggregate_confidence_delta'], record['stability_factor']
        
        # Try to find the nearest match by country and domain only
        for stored_key, record in self.data['learning_records'].items():
            if record['country'] == country and record['domain'] == domain:
                return record['aggregate_confidence_delta'], record['stability_factor']
        
        # Return neutral values if no match found
        return 0.0, 0.1  # Small stability for new combinations
    
    def update_confidence_delta(self, country: str, domain: str, procedure_id: str, delta: float) -> None:
        """Update the aggregate confidence delta for a specific context"""
        key = f"{country}:{domain}:{procedure_id}"
        
        if key not in self.data['learning_records']:
            self.data['learning_records'][key] = {
                'country': country,
                'domain': domain,
                'procedure_id': procedure_id,
                'aggregate_confidence_delta': 0.0,
                'success_count': 0,
                'failure_count': 0,
                'stability_factor': 0.1,
                'last_updated': None,
                'history': []
            }
        
        record = self.data['learning_records'][key]
        # Apply bounded learning with gradual adjustment
        old_delta = record['aggregate_confidence_delta']
        # Adjust gradually to prevent large swings from single signals
        adjustment_rate = min(0.1, record['stability_factor'] * 0.2)
        new_delta = old_delta + (delta - old_delta) * adjustment_rate
        record['aggregate_confidence_delta'] = max(-0.5, min(0.5, new_delta))
        record['last_updated'] = datetime.utcnow().isoformat()
        
        self._save_data()
    
    def get_record_stats(self, country: str, domain: str, procedure_id: str) -> Optional[Dict]:
        """Get statistics for a specific record"""
        key = f"{country}:{domain}:{procedure_id}"
        if key in self.data['learning_records']:
            return self.data['learning_records'][key]
        return None