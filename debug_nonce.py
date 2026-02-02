from provenance_chain.nonce_manager import nonce_manager
import time

def debug_validate_nonce(nonce: str) -> bool:
    print(f'DEBUG: Validating nonce "{nonce}"')
    current_time = time.time()
    print(f'DEBUG: Current time: {current_time}')
    
    with nonce_manager.lock:
        nonce_key = None
        print(f'DEBUG: Checking {len(nonce_manager.used_nonces)} stored entries')
        for i, stored in enumerate(nonce_manager.used_nonces):
            print(f'DEBUG: Entry {i}: "{stored}"')
            if stored.startswith(f'{nonce}:'):
                nonce_key = stored
                print(f'DEBUG: Found matching entry: "{nonce_key}"')
                break
        
        if nonce_key is None:
            print('DEBUG: Nonce not found in used_nonces')
            return False
        
        # Check if already used
        if nonce_key.endswith(':used'):
            print('DEBUG: Nonce already marked as used')
            return False
        
        # Check TTL
        parts = nonce_key.split(':')
        if len(parts) < 2:
            print('DEBUG: Invalid nonce key format')
            return False
            
        timestamp_str = parts[1]
        print(f'DEBUG: Timestamp string: "{timestamp_str}"')
        if not timestamp_str.replace('.', '').isdigit():
            print('DEBUG: Invalid timestamp format')
            return False
        
        timestamp = float(timestamp_str)
        age = current_time - timestamp
        print(f'DEBUG: Timestamp: {timestamp}, Age: {age:.3f}s')
        print(f'DEBUG: TTL: {nonce_manager.ttl_seconds}s')
        if age > nonce_manager.ttl_seconds:
            print(f'DEBUG: Nonce expired (TTL: {nonce_manager.ttl_seconds}s)')
            nonce_manager.used_nonces.discard(nonce_key)
            return False
        
        # Mark as used
        print('DEBUG: Nonce is valid, marking as used')
        nonce_manager.used_nonces.discard(nonce_key)
        nonce_manager.used_nonces.add(f'{nonce}:{timestamp}:used')
        return True

# Test the debug function
print("=== Nonce Debug Test ===")
nonce = nonce_manager.generate_nonce()
print(f'Generated nonce: {nonce}')

# Use our debug function
result = debug_validate_nonce(nonce)
print(f'Debug validation result: {result}')

# Also test the original function
original_result = nonce_manager.validate_nonce(nonce)
print(f'Original validation result: {original_result}')