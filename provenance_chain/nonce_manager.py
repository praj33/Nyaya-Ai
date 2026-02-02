import uuid
import time
import threading
from typing import Set, Dict
import os

class NonceManager:
    def __init__(self, ttl_seconds: int = 600):  # 10 minutes default
        self.ttl_seconds = int(os.getenv('NONCE_TTL_SECONDS', ttl_seconds))
        self.pending_nonces: Dict[str, float] = {}  # nonce -> timestamp
        self.used_nonces: Set[str] = set()  # nonce values that have been used
        self.lock = threading.Lock()
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_nonces, daemon=True)
        self.cleanup_thread.start()

    def generate_nonce(self) -> str:
        """Generate a new unique nonce."""
        nonce = str(uuid.uuid4())
        timestamp = time.time()
        with self.lock:
            self.pending_nonces[nonce] = timestamp
        return nonce

    def validate_nonce(self, nonce: str) -> bool:
        """Validate a nonce - must be unused and within TTL."""
        current_time = time.time()
        print(f"DEBUG: validate_nonce called with nonce='{nonce}'")
        print(f"DEBUG: current_time={current_time}")
        print(f"DEBUG: pending_nonces count={len(self.pending_nonces)}")
        print(f"DEBUG: used_nonces count={len(self.used_nonces)}")
            
        with self.lock:
            # Check if already used
            if nonce in self.used_nonces:
                print("DEBUG: nonce already used, returning False")
                return False
                
            # Check if pending
            if nonce not in self.pending_nonces:
                print("DEBUG: nonce not found in pending, returning False")
                return False
                
            # Check TTL
            timestamp = self.pending_nonces[nonce]
            age = current_time - timestamp
            print(f"DEBUG: timestamp={timestamp}, age={age}")
            if age > self.ttl_seconds:
                print(f"DEBUG: nonce expired (TTL={self.ttl_seconds}), returning False")
                del self.pending_nonces[nonce]  # Remove expired
                return False
                
            # Move from pending to used
            print("DEBUG: nonce is valid, marking as used")
            del self.pending_nonces[nonce]
            self.used_nonces.add(nonce)
            return True

    def _cleanup_expired_nonces(self):
        """Background thread to clean up expired nonces."""
        while True:
            time.sleep(60)  # Clean up every minute
            current_time = time.time()

            with self.lock:
                # Clean up expired pending nonces
                expired_pending = []
                for nonce, timestamp in self.pending_nonces.items():
                    if current_time - timestamp > self.ttl_seconds:
                        expired_pending.append(nonce)
                
                for nonce in expired_pending:
                    del self.pending_nonces[nonce]
                
                # Clean up old used nonces (keep them for a bit longer to prevent replays)
                # We can keep used nonces for 2x TTL to ensure no replays
                if len(self.used_nonces) > 1000:  # Cleanup if too many
                    # For simplicity, we'll just keep the most recent ones
                    # In production, you might want a more sophisticated approach
                    self.used_nonces.clear()

# Global instance
nonce_manager = NonceManager()