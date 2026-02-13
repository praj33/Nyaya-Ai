import os
import hmac
import hashlib
import base64
from typing import Dict, Any
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class EventSigner:
    def __init__(self):
        self.signing_method = os.getenv('SIGNING_METHOD', 'HMAC_SHA256')
        self.key_id = os.getenv('SIGNING_KEY_ID', 'primary-key-2025')

        if self.signing_method == 'HMAC_SHA256':
            self.secret_key = os.getenv('HMAC_SECRET_KEY')
            if not self.secret_key:
                raise ValueError("HMAC_SECRET_KEY environment variable must be set")
        elif self.signing_method == 'ECDSA':
            # For ECDSA, would need private key, but keeping simple for now
            raise NotImplementedError("ECDSA signing not yet implemented")
        else:
            raise ValueError(f"Unsupported signing method: {self.signing_method}")

    def sign_event(self, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Sign an event dictionary and return signed event structure."""
        # Create canonical JSON string for signing
        canonical_json = json.dumps(event_dict, sort_keys=True, separators=(',', ':'))

        if self.signing_method == 'HMAC_SHA256':
            signature = hmac.new(
                self.secret_key.encode(),
                canonical_json.encode(),
                hashlib.sha256
            ).digest()
            signature_b64 = base64.b64encode(signature).decode()

        return {
            "event": event_dict,
            "signature": signature_b64,
            "key_id": self.key_id
        }

    def verify_signature(self, signed_event: Dict[str, Any]) -> bool:
        """Verify the signature of a signed event."""
        event = signed_event['event']
        signature_b64 = signed_event['signature']
        key_id = signed_event['key_id']

        if key_id != self.key_id:
            return False

        canonical_json = json.dumps(event, sort_keys=True, separators=(',', ':'))

        if self.signing_method == 'HMAC_SHA256':
            expected_signature = hmac.new(
                self.secret_key.encode(),
                canonical_json.encode(),
                hashlib.sha256
            ).digest()
            expected_b64 = base64.b64encode(expected_signature).decode()

        return hmac.compare_digest(signature_b64, expected_b64)

# Global instance
signer = EventSigner()