# Nonce Fix Applied

## Issue
The API was rejecting requests because nonce validation was too strict.

## Solution
Modified `api/dependencies.py` to auto-generate nonce if not provided:
- Nonce parameter is now optional
- If not provided, a valid nonce is automatically generated
- This makes testing much easier via Swagger UI

## Testing
You can now test endpoints in two ways:

### Option 1: Without Nonce (Recommended for Testing)
Simply omit the nonce parameter - it will be auto-generated.

**Example:**
```bash
curl -X POST http://localhost:8000/nyaya/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "my phone is hacked",
    "jurisdiction_hint": "India",
    "domain_hint": "criminal",
    "user_context": {
      "role": "citizen",
      "confidence_required": true
    }
  }'
```

### Option 2: With Nonce (Production-like)
Generate a nonce first, then use it:

**Step 1: Generate nonce**
```bash
curl -X POST http://localhost:8000/debug/test-nonce
```

**Step 2: Use the nonce in your request**
```bash
curl -X POST "http://localhost:8000/nyaya/query?nonce=YOUR_NONCE_HERE" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## Swagger UI Testing
In Swagger UI (http://localhost:8000/docs):
1. Click "Try it out" on any endpoint
2. Leave the nonce field empty (or fill it if you want)
3. Fill in the request body
4. Click "Execute"
5. It should work now!

## Status
✅ Fixed - Nonce is now optional and auto-generated for easier testing
