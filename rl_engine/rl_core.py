"""
Reinforcement Learning Core for Nyaya AI
Country-agnostic learning backbone that silently improves over time
"""
import threading
from datetime import datetime
from typing import Dict
from .learning_store import LearningStore
from .reward_engine import RewardEngine


class RLCores:
    """Singleton RL Core with thread-safe operations"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RLCores, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.learning_store = LearningStore()
        self.reward_engine = RewardEngine()
        self._initialized = True
        self._thread_lock = threading.Lock()


def update_learning(signal_payload: Dict) -> Dict:
    """
    Receive learning signal and update the RL system with hardening
    
    Args:
        signal_payload: Dictionary with learning signal data
    
    Returns:
        Dict: Result with learning status and details
    """
    rl_core = RLCores()
    
    with rl_core._thread_lock:
        # Get the context for this signal
        country = signal_payload.get('country', 'unknown')
        domain = signal_payload.get('domain', 'unknown')
        procedure_id = signal_payload.get('procedure_id', 'unknown')
        
        # Get recent feedback history for anomaly detection
        recent_history = rl_core.learning_store.get_recent_feedback_history(country, domain, procedure_id)
        
        # Get current stability factor and variance for this context
        current_time = datetime.utcnow()
        current_delta, stability_factor = rl_core.learning_store.get_adjustment_for_context(
            country, domain, procedure_id, current_time
        )
        
        # Calculate current variance for volatility protection
        record_stats = rl_core.learning_store.get_record_stats(country, domain, procedure_id, current_time)
        current_variance = 0.0
        if record_stats and 'history' in record_stats:
            if len(record_stats['history']) > 1:
                deltas = [entry.get('confidence_delta', 0.0) for entry in record_stats['history'][-10:]]
                if deltas:
                    mean_delta = sum(deltas) / len(deltas)
                    current_variance = sum((d - mean_delta) ** 2 for d in deltas) / len(deltas)
        
        # Calculate the confidence delta with all protections
        original_confidence = signal_payload.get('confidence_before', 0.5)
        confidence_delta, should_learn, rejection_reason = rl_core.reward_engine.get_confidence_delta(
            original_confidence, 
            signal_payload, 
            stability_factor,
            recent_history,
            current_variance
        )
        
        result = {
            'should_learn': should_learn,
            'rejection_reason': rejection_reason,
            'confidence_delta': confidence_delta,
            'original_confidence': original_confidence,
            'applied_delta': 0.0
        }
        
        if should_learn and confidence_delta != 0.0:
            # Store the raw signal
            rl_core.learning_store.store_signal(signal_payload)
            
            # Update the learning store with the new confidence delta
            rl_core.learning_store.update_confidence_delta(
                country, domain, procedure_id, confidence_delta, current_time
            )
            
            # Update the last entry in history with the confidence delta
            key = f"{country}:{domain}:{procedure_id}"
            if key in rl_core.learning_store.data['learning_records']:
                record = rl_core.learning_store.data['learning_records'][key]
                if record['history']:
                    # Update the most recent entry with the confidence delta that was applied
                    record['history'][-1]['confidence_delta'] = confidence_delta
                    rl_core.learning_store._save_data()
            
            result['applied_delta'] = confidence_delta
            result['status'] = 'learning_applied'
        else:
            result['status'] = 'learning_rejected' if not should_learn else 'no_change'
        
        return result


def get_adjusted_confidence(case_context: Dict) -> Dict:
    """
    Get the confidence adjusted by the RL system with hardening
    
    Args:
        case_context: Dictionary with context data (country, domain, procedure_id, original_confidence)
    
    Returns:
        Dict: Adjusted confidence with metadata
    """
    rl_core = RLCores()
    
    with rl_core._thread_lock:
        # Extract context information
        country = case_context.get('country', 'unknown')
        domain = case_context.get('domain', 'unknown')
        procedure_id = case_context.get('procedure_id', 'unknown')
        original_confidence = case_context.get('original_confidence', 0.5)
        
        # Get the learned adjustment for this context with decay
        current_time = datetime.utcnow()
        confidence_delta, stability_factor = rl_core.learning_store.get_adjustment_for_context(
            country, domain, procedure_id, current_time
        )
        
        # Apply the adjustment to the original confidence
        adjusted_confidence = original_confidence + confidence_delta
        
        # Bound the result between 0 and 1
        bounded_confidence = max(0.0, min(1.0, adjusted_confidence))
        
        # Get additional metadata
        record_stats = rl_core.learning_store.get_record_stats(country, domain, procedure_id, current_time)
        
        return {
            'adjusted_confidence': bounded_confidence,
            'original_confidence': original_confidence,
            'confidence_delta': confidence_delta,
            'stability_factor': stability_factor,
            'time_since_last_update': record_stats.get('time_since_last_update', 'unknown') if record_stats else 'unknown',
            'current_decayed_delta': record_stats.get('current_decayed_delta', 0.0) if record_stats else 0.0
        }