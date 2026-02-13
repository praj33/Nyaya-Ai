import json
import hashlib
from datetime import datetime
import uuid

def add_ledger_entry(file_path, entry_type, trace_id, details):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Get last hash
    prev_hash = data[-1]['hash'] if data else "GENESIS"
    
    # Create new entry
    new_entry = {
        "type": entry_type,
        "timestamp": datetime.now().isoformat(),
        "trace_id": trace_id,
        "prev_hash": prev_hash
    }
    
    # Add type-specific details
    if entry_type == "routing_decision":
        new_entry["routing_details"] = details
    elif entry_type == "refusal_or_escalation":
        new_entry["refusal_details"] = details
    
    # Calculate hash
    entry_str = json.dumps(new_entry, sort_keys=True)
    new_entry["hash"] = hashlib.sha256(entry_str.encode()).hexdigest()
    
    # Add to data
    data.append(new_entry)
    
    # Write back
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return new_entry["hash"]

# Add some new entries
file_path = "enforcement_ledger.json"

# Add routing decision
trace_id = str(uuid.uuid4())
add_ledger_entry(file_path, "routing_decision", trace_id, {
    "query": "What are privacy laws in India?",
    "jurisdiction_hint": "India",
    "domain_hint": "privacy",
    "target_jurisdiction": "IN",
    "target_agent": "india_legal_agent"
})

# Add corresponding refusal
add_ledger_entry(file_path, "refusal_or_escalation", trace_id, {
    "reason": "enforcement_blocked",
    "query": "What are privacy laws in India?",
    "target_jurisdiction": "IN"
})

# Add rate limit refusal
add_ledger_entry(file_path, "refusal_or_escalation", "rate-limit-trace", {
    "reason": "enforcement_blocked_rl",
    "trace_id": "rate-limit-trace",
    "rating": 5
})

print("Added 3 new entries to enforcement ledger")