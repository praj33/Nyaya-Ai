import json
import os

class DisputeTypeMatcher:
    def __init__(self):
        dataset_path = os.path.join(os.path.dirname(__file__), "db", "indian_law_dataset.json")
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.dispute_types = data.get('civil_law', {})
    
    def detect_dispute_type(self, query: str) -> str:
        """Detect dispute type from query"""
        query_lower = query.lower()
        
        # Banking disputes
        if any(word in query_lower for word in ['bank', 'deposit', 'fd', 'account', 'cheque', 'loan', 'credit card']):
            return 'banking_disputes'
        
        # Insurance disputes
        if any(word in query_lower for word in ['insurance', 'policy', 'claim', 'premium']):
            return 'insurance_disputes'
        
        # Medical negligence
        if any(word in query_lower for word in ['doctor', 'hospital', 'medical', 'treatment', 'surgery', 'negligence']):
            return 'medical_negligence'
        
        # Consumer disputes
        if any(word in query_lower for word in ['defective', 'product', 'warranty', 'consumer', 'refund']):
            return 'consumer_disputes'
        
        # Employment
        if any(word in query_lower for word in ['salary', 'fired', 'termination', 'employer', 'workplace']):
            return 'employment_law'
        
        return None
    
    def get_dispute_info(self, dispute_type: str):
        """Get law, remedies, and process steps for dispute type"""
        if dispute_type and dispute_type in self.dispute_types:
            return self.dispute_types[dispute_type]
        return None
