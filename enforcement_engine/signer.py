"""
Cryptographic Signer for Enforcement Decisions
Provides cryptographic proof for all enforcement decisions
"""
import hmac
import hashlib
import os
import json
from typing import Dict, Any
from datetime import datetime
from .decision_model import EnforcementResult


class EnforcementSigner:
    """Handles cryptographic signing of enforcement decisions"""
    
    def __init__(self, secret_key: str = None):
        if secret_key is None:
            secret_key = os.getenv('HMAC_SECRET_KEY', 'default_enforcement_key')
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
    
    def sign_decision(self, decision_data: Dict[str, Any]) -> str:
        """Sign decision data using HMAC-SHA256"""
        # Convert decision data to JSON string for consistent hashing
        json_str = json.dumps(decision_data, sort_keys=True, default=str)
        signature = hmac.new(
            self.secret_key,
            json_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signature(self, decision_data: Dict[str, Any], signature: str) -> bool:
        """Verify that the signature matches the decision data"""
        expected_signature = self.sign_decision(decision_data)
        return hmac.compare_digest(expected_signature, signature)
    
    def create_signed_decision_object(self, result: EnforcementResult) -> Dict[str, Any]:
        """Create a signed decision object with cryptographic proof"""
        decision_obj = {
            'decision': result.decision.value,
            'rule_id': result.rule_id,
            'policy_source': result.policy_source.value,
            'reasoning_summary': result.reasoning_summary,
            'trace_id': result.trace_id,
            'timestamp': result.timestamp.isoformat(),
            'metadata': result.metadata or {}
        }
        
        # Add signature
        signature = self.sign_decision(decision_obj)
        decision_obj['signature'] = signature
        
        # Add signing key identifier
        decision_obj['signing_key_id'] = 'enforcement-primary-key'
        
        return decision_obj
    
    def create_enforcement_proof(self, result: EnforcementResult) -> Dict[str, Any]:
        """Create a complete enforcement proof"""
        proof = {
            'decision_summary': result.to_dict(),
            'cryptographic_signature': result.signed_decision_object.get('signature'),
            'proof_hash': result.proof_hash,
            'verification_data': {
                'algorithm': 'HMAC-SHA256',
                'signing_key_used': result.signed_decision_object.get('signing_key_id'),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        return proof