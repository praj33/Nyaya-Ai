"""
Cryptographic Signer for Enforcement Provenance
Signs and verifies all enforcement-related events
"""
import hmac
import hashlib
import os
import json
from typing import Dict, Any
from datetime import datetime


class EnforcementProvenanceSigner:
    """Handles cryptographic signing of enforcement provenance events"""
    
    def __init__(self, secret_key: str = None):
        if secret_key is None:
            secret_key = os.getenv('HMAC_SECRET_KEY', 'default_enforcement_key')
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
    
    def sign_event(self, event_data: Dict[str, Any]) -> str:
        """Sign event data using HMAC-SHA256"""
        json_str = json.dumps(event_data, sort_keys=True, default=str)
        signature = hmac.new(
            self.secret_key,
            json_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, event_data: Dict[str, Any], signature: str) -> bool:
        """Verify that the signature matches the event data"""
        expected_signature = self.sign_event(event_data)
        return hmac.compare_digest(expected_signature, signature)
    
    def create_signed_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a signed event with cryptographic proof"""
        signed_event = {
            'type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': event_data,
            'signature': self.sign_event(event_data),
            'signing_key_id': 'enforcement-provenance-key',
            'algorithm': 'HMAC-SHA256'
        }
        
        return signed_event


# Global signer instance
enforcement_signer = EnforcementProvenanceSigner()


def sign_enforcement_event(event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sign an enforcement event"""
    return enforcement_signer.create_signed_event(event_type, event_data)