"""
Verifier for Enforcement Provenance
Verifies authenticity and integrity of enforcement events
"""
import hmac
import hashlib
import os
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime


class EnforcementProvenanceVerifier:
    """Verifies authenticity and integrity of enforcement provenance events"""
    
    def __init__(self, secret_key: str = None):
        if secret_key is None:
            secret_key = os.getenv('HMAC_SECRET_KEY', 'default_enforcement_key')
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
    
    def verify_signature(self, event_data: Dict[str, Any], signature: str) -> bool:
        """Verify the signature of an event"""
        expected_signature = self._calculate_signature(event_data)
        return hmac.compare_digest(expected_signature, signature)
    
    def _calculate_signature(self, event_data: Dict[str, Any]) -> str:
        """Calculate signature for event data"""
        # We need to exclude the signature itself from the calculation
        data_to_verify = event_data.copy()
        if 'signature' in data_to_verify:
            del data_to_verify['signature']
        if 'signing_key_id' in data_to_verify:
            del data_to_verify['signing_key_id']
        if 'algorithm' in data_to_verify:
            del data_to_verify['algorithm']
        
        json_str = json.dumps(data_to_verify, sort_keys=True, default=str)
        signature = hmac.new(
            self.secret_key,
            json_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_signed_event(self, signed_event: Dict[str, Any]) -> Tuple[bool, str]:
        """Verify a complete signed event"""
        if 'signature' not in signed_event:
            return False, "Missing signature"
        
        if 'data' not in signed_event:
            return False, "Missing event data"
        
        signature = signed_event['signature']
        event_data = signed_event['data']
        
        is_valid = self.verify_signature(event_data, signature)
        
        if not is_valid:
            return False, "Invalid signature"
        
        return True, "Valid signature"
    
    def verify_event_chain(self, event_chain: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Verify the integrity of an event chain"""
        if not event_chain:
            return True, "Empty chain is valid"
        
        # Verify each event in the chain
        for i, event in enumerate(event_chain):
            is_valid, message = self.verify_signed_event(event)
            if not is_valid:
                return False, f"Event {i} invalid: {message}"
        
        # Verify hash chain if prev_hash is available
        for i in range(1, len(event_chain)):
            prev_event = event_chain[i-1]
            curr_event = event_chain[i]
            
            # Check if prev_hash matches the hash of the previous event
            if 'hash' in prev_event and 'prev_hash' in curr_event:
                if prev_event['hash'] != curr_event['prev_hash']:
                    return False, f"Hash chain broken between events {i-1} and {i}"
        
        return True, "Valid chain"
    
    def verify_trace_integrity(self, trace_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify the complete integrity of a trace"""
        verification_results = {
            'overall_validity': True,
            'events_verified': 0,
            'invalid_events': [],
            'chain_integrity': True,
            'timestamp_validity': True
        }
        
        # Verify each event
        for i, event in enumerate(trace_events):
            is_valid, message = self.verify_signed_event(event)
            verification_results['events_verified'] += 1
            
            if not is_valid:
                verification_results['overall_validity'] = False
                verification_results['invalid_events'].append({
                    'index': i,
                    'event_type': event.get('type', 'unknown'),
                    'error': message
                })
        
        # Verify chain integrity
        chain_valid, chain_msg = self.verify_event_chain(trace_events)
        verification_results['chain_integrity'] = chain_valid
        
        if not chain_valid:
            verification_results['overall_validity'] = False
        
        # Verify timestamps are in order (optional check)
        timestamps = []
        for event in trace_events:
            if 'timestamp' in event:
                timestamps.append(event['timestamp'])
        
        # Check if timestamps are roughly in chronological order
        sorted_timestamps = sorted(timestamps)
        if timestamps != sorted_timestamps:
            verification_results['timestamp_validity'] = False
            verification_results['overall_validity'] = False
        
        return verification_results


# Global verifier instance
enforcement_verifier = EnforcementProvenanceVerifier()


def verify_enforcement_event(signed_event: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify a single enforcement event"""
    return enforcement_verifier.verify_signed_event(signed_event)


def verify_event_chain_integrity(event_chain: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Verify the integrity of an event chain"""
    return enforcement_verifier.verify_event_chain(event_chain)


def verify_trace_full_integrity(trace_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify the full integrity of a trace"""
    return enforcement_verifier.verify_trace_integrity(trace_events)