"""
Enforcement Provenance Ledger
Append-only, hash-chained ledger for all enforcement decisions
"""
import json
import hashlib
import os
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..enforcement_engine.decision_model import EnforcementResult


class EnforcementLedger:
    """Immutable ledger for enforcement decisions"""
    
    def __init__(self, ledger_path: str = "enforcement_ledger.json"):
        self.ledger_path = ledger_path
        self.lock = threading.Lock()
        self._load_ledger()
    
    def _load_ledger(self):
        """Load the ledger from persistent storage"""
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, 'r') as f:
                    self.entries = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.entries = []
        else:
            self.entries = []
        
        # Validate ledger integrity
        self._validate_chain()
    
    def _save_ledger(self):
        """Save the ledger to persistent storage"""
        try:
            with open(self.ledger_path, 'w') as f:
                json.dump(self.entries, f, indent=2)
        except IOError:
            # Fail silently to prevent disrupting operations
            pass
    
    def _validate_chain(self):
        """Validate the hash chain integrity"""
        for i in range(1, len(self.entries)):
            prev_entry = self.entries[i-1]
            curr_entry = self.entries[i]
            
            expected_prev_hash = prev_entry.get('hash')
            actual_prev_hash = curr_entry.get('prev_hash')
            
            if expected_prev_hash != actual_prev_hash:
                # Ledger has been tampered with - truncate at the point of corruption
                self.entries = self.entries[:i-1]
                break
    
    def _calculate_hash(self, entry: Dict[str, Any]) -> str:
        """Calculate hash for an entry"""
        # Remove existing hash to avoid circular dependency
        entry_copy = entry.copy()
        entry_copy.pop('hash', None)
        
        json_str = json.dumps(entry_copy, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def append_enforcement_decision(self, result: EnforcementResult, additional_data: Optional[Dict[str, Any]] = None) -> str:
        """Append an enforcement decision to the ledger"""
        with self.lock:
            # Create ledger entry
            entry = {
                'type': 'enforcement_decision',
                'timestamp': datetime.utcnow().isoformat(),
                'decision': result.decision.value,
                'rule_id': result.rule_id,
                'policy_source': result.policy_source.value,
                'reasoning_summary': result.reasoning_summary,
                'trace_id': result.trace_id,
                'proof_hash': result.proof_hash,
                'signed_decision_object': result.signed_decision_object,
                'additional_data': additional_data or {}
            }
            
            # Add previous hash if ledger is not empty
            if self.entries:
                entry['prev_hash'] = self.entries[-1]['hash']
            else:
                entry['prev_hash'] = 'GENESIS'
            
            # Calculate hash for this entry
            entry['hash'] = self._calculate_hash(entry)
            
            # Append to ledger
            self.entries.append(entry)
            
            # Save to persistent storage
            self._save_ledger()
            
            return entry['hash']
    
    def append_agent_execution(self, trace_id: str, execution_details: Dict[str, Any]) -> str:
        """Append an agent execution to the ledger"""
        with self.lock:
            entry = {
                'type': 'agent_execution',
                'timestamp': datetime.utcnow().isoformat(),
                'trace_id': trace_id,
                'execution_details': execution_details
            }
            
            # Add previous hash if ledger is not empty
            if self.entries:
                entry['prev_hash'] = self.entries[-1]['hash']
            else:
                entry['prev_hash'] = 'GENESIS'
            
            # Calculate hash for this entry
            entry['hash'] = self._calculate_hash(entry)
            
            # Append to ledger
            self.entries.append(entry)
            
            # Save to persistent storage
            self._save_ledger()
            
            return entry['hash']
    
    def append_routing_decision(self, trace_id: str, routing_details: Dict[str, Any]) -> str:
        """Append a routing decision to the ledger"""
        with self.lock:
            entry = {
                'type': 'routing_decision',
                'timestamp': datetime.utcnow().isoformat(),
                'trace_id': trace_id,
                'routing_details': routing_details
            }
            
            # Add previous hash if ledger is not empty
            if self.entries:
                entry['prev_hash'] = self.entries[-1]['hash']
            else:
                entry['prev_hash'] = 'GENESIS'
            
            # Calculate hash for this entry
            entry['hash'] = self._calculate_hash(entry)
            
            # Append to ledger
            self.entries.append(entry)
            
            # Save to persistent storage
            self._save_ledger()
            
            return entry['hash']
    
    def append_rl_update(self, trace_id: str, rl_details: Dict[str, Any]) -> str:
        """Append an RL update to the ledger"""
        with self.lock:
            entry = {
                'type': 'rl_update',
                'timestamp': datetime.utcnow().isoformat(),
                'trace_id': trace_id,
                'rl_details': rl_details
            }
            
            # Add previous hash if ledger is not empty
            if self.entries:
                entry['prev_hash'] = self.entries[-1]['hash']
            else:
                entry['prev_hash'] = 'GENESIS'
            
            # Calculate hash for this entry
            entry['hash'] = self._calculate_hash(entry)
            
            # Append to ledger
            self.entries.append(entry)
            
            # Save to persistent storage
            self._save_ledger()
            
            return entry['hash']
    
    def append_refusal_or_escalation(self, trace_id: str, refusal_details: Dict[str, Any]) -> str:
        """Append a refusal or escalation to the ledger"""
        with self.lock:
            entry = {
                'type': 'refusal_or_escalation',
                'timestamp': datetime.utcnow().isoformat(),
                'trace_id': trace_id,
                'refusal_details': refusal_details
            }
            
            # Add previous hash if ledger is not empty
            if self.entries:
                entry['prev_hash'] = self.entries[-1]['hash']
            else:
                entry['prev_hash'] = 'GENESIS'
            
            # Calculate hash for this entry
            entry['hash'] = self._calculate_hash(entry)
            
            # Append to ledger
            self.entries.append(entry)
            
            # Save to persistent storage
            self._save_ledger()
            
            return entry['hash']
    
    def get_trace_chain(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get the complete chain of events for a trace"""
        trace_entries = []
        for entry in self.entries:
            if entry.get('trace_id') == trace_id:
                trace_entries.append(entry)
        return trace_entries
    
    def verify_integrity(self) -> bool:
        """Verify the integrity of the entire ledger"""
        try:
            for i in range(1, len(self.entries)):
                prev_entry = self.entries[i-1]
                curr_entry = self.entries[i]
                
                # Check hash chain
                expected_prev_hash = prev_entry.get('hash')
                actual_prev_hash = curr_entry.get('prev_hash')
                
                if expected_prev_hash != actual_prev_hash:
                    return False
                
                # Recalculate current hash to verify it hasn't been tampered with
                calculated_hash = self._calculate_hash(curr_entry)
                if calculated_hash != curr_entry['hash']:
                    return False
            
            return True
        except Exception:
            return False


# Global ledger instance
enforcement_ledger = EnforcementLedger()


def log_enforcement_decision(result: EnforcementResult, additional_data: Optional[Dict[str, Any]] = None) -> str:
    """Log an enforcement decision to the ledger"""
    return enforcement_ledger.append_enforcement_decision(result, additional_data)


def log_agent_execution(trace_id: str, execution_details: Dict[str, Any]) -> str:
    """Log an agent execution to the ledger"""
    return enforcement_ledger.append_agent_execution(trace_id, execution_details)


def log_routing_decision(trace_id: str, routing_details: Dict[str, Any]) -> str:
    """Log a routing decision to the ledger"""
    return enforcement_ledger.append_routing_decision(trace_id, routing_details)


def log_rl_update(trace_id: str, rl_details: Dict[str, Any]) -> str:
    """Log an RL update to the ledger"""
    return enforcement_ledger.append_rl_update(trace_id, rl_details)


def log_refusal_or_escalation(trace_id: str, refusal_details: Dict[str, Any]) -> str:
    """Log a refusal or escalation to the ledger"""
    return enforcement_ledger.append_refusal_or_escalation(trace_id, refusal_details)


def get_trace_history(trace_id: str) -> List[Dict[str, Any]]:
    """Get the complete history for a trace"""
    return enforcement_ledger.get_trace_chain(trace_id)


def verify_ledger_integrity() -> bool:
    """Verify the integrity of the entire ledger"""
    return enforcement_ledger.verify_integrity()