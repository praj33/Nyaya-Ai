from fastapi import APIRouter

debug_router = APIRouter(prefix="/debug", tags=["debug"])

@debug_router.get("/nonce-state")
async def get_nonce_state():
    """Debug endpoint to check nonce manager state"""
    from provenance_chain.nonce_manager import nonce_manager
    return {
        "pending_nonces_count": len(nonce_manager.pending_nonces),
        "pending_nonces": list(nonce_manager.pending_nonces.keys()),
        "used_nonces_count": len(nonce_manager.used_nonces),
        "used_nonces": list(nonce_manager.used_nonces),
        "ttl_seconds": nonce_manager.ttl_seconds,
        "instance_id": id(nonce_manager)
    }

@debug_router.post("/test-nonce")
async def test_nonce_generation():
    """Debug endpoint to test nonce generation and validation"""
    from provenance_chain.nonce_manager import nonce_manager
    import time
    
    # Generate nonce
    nonce = nonce_manager.generate_nonce()
    
    # Validate it
    is_valid = nonce_manager.validate_nonce(nonce)
    
    return {
        "generated_nonce": nonce,
        "validation_result": is_valid,
        "pending_nonces_count": len(nonce_manager.pending_nonces),
        "used_nonces_count": len(nonce_manager.used_nonces),
        "current_time": time.time(),
        "instance_id": id(nonce_manager)
    }

@debug_router.get("/generate-nonce")
async def generate_nonce():
    """Endpoint to generate a valid nonce for testing"""
    from provenance_chain.nonce_manager import nonce_manager
    
    nonce = nonce_manager.generate_nonce()
    
    return {
        "nonce": nonce,
        "message": "Use this nonce in your next API request",
        "expires_in_seconds": nonce_manager.ttl_seconds
    }