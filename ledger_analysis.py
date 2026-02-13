import json
from datetime import datetime
from collections import Counter, defaultdict

def analyze_enforcement_ledger(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Basic stats
    total_entries = len(data)
    routing_decisions = sum(1 for entry in data if entry['type'] == 'routing_decision')
    refusals = sum(1 for entry in data if entry['type'] == 'refusal_or_escalation')
    
    # Refusal reasons
    refusal_reasons = Counter()
    jurisdictions = Counter()
    queries = []
    
    for entry in data:
        if entry['type'] == 'refusal_or_escalation':
            reason = entry['refusal_details']['reason']
            refusal_reasons[reason] += 1
            
            if 'target_jurisdiction' in entry['refusal_details']:
                jurisdictions[entry['refusal_details']['target_jurisdiction']] += 1
                
            if 'query' in entry['refusal_details'] and entry['refusal_details']['query'] != 'string':
                queries.append(entry['refusal_details']['query'])
    
    # Time analysis
    timestamps = [datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')) for entry in data]
    time_span = max(timestamps) - min(timestamps)
    
    print("=== ENFORCEMENT LEDGER ANALYSIS ===")
    print(f"Total entries: {total_entries}")
    print(f"Routing decisions: {routing_decisions}")
    print(f"Refusals/escalations: {refusals}")
    print(f"Time span: {time_span}")
    print(f"\nRefusal reasons: {dict(refusal_reasons)}")
    print(f"Affected jurisdictions: {dict(jurisdictions)}")
    print(f"Unique queries blocked: {len(set(queries))}")
    
    # Hash chain validation
    print(f"\n=== HASH CHAIN VALIDATION ===")
    valid_chain = True
    for i in range(1, len(data)):
        if data[i]['prev_hash'] != data[i-1]['hash']:
            print("X Chain break at entry {}".format(i))
            valid_chain = False
    
    if valid_chain:
        print("Hash chain is valid")
    
    return {
        'total_entries': total_entries,
        'routing_decisions': routing_decisions,
        'refusals': refusals,
        'refusal_reasons': dict(refusal_reasons),
        'jurisdictions': dict(jurisdictions),
        'unique_queries': len(set(queries)),
        'valid_chain': valid_chain
    }

if __name__ == "__main__":
    analyze_enforcement_ledger("enforcement_ledger.json")