"""
Reinforcement Learning Core for Nyaya AI
Country-agnostic learning backbone that silently improves over time
"""
import threading
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


def update_learning(signal_payload: Dict) -> None:
    """
    Receive learning signal and update the RL system
    
    Args:
        signal_payload: Dictionary with learning signal data
    """
    rl_core = RLCores()
    
    with rl_core._thread_lock:
        # Store the raw signal
        rl_core.learning_store.store_signal(signal_payload)
        
        # Compute reward based on the signal
        reward = rl_core.reward_engine.compute_reward(signal_payload)
        
        # Get the context for this signal
        country = signal_payload.get('country', 'unknown')
        domain = signal_payload.get('domain', 'unknown')
        procedure_id = signal_payload.get('procedure_id', 'unknown')
        
        # Get current stability factor for this context
        _, stability_factor = rl_core.learning_store.get_adjustment_for_context(country, domain, procedure_id)
        
        # Calculate the confidence delta based on the signal
        original_confidence = signal_payload.get('confidence_before', 0.5)
        confidence_delta = rl_core.reward_engine.get_confidence_delta(
            original_confidence, signal_payload, stability_factor
        )
        
        # Update the learning store with the new confidence delta
        rl_core.learning_store.update_confidence_delta(country, domain, procedure_id, confidence_delta)


def get_adjusted_confidence(case_context: Dict) -> float:
    """
    Get the confidence adjusted by the RL system
    
    Args:
        case_context: Dictionary with context data (country, domain, procedure_id, original_confidence)
    
    Returns:
        float: Adjusted confidence value
    """
    rl_core = RLCores()
    
    with rl_core._thread_lock:
        # Extract context information
        country = case_context.get('country', 'unknown')
        domain = case_context.get('domain', 'unknown')
        procedure_id = case_context.get('procedure_id', 'unknown')
        original_confidence = case_context.get('original_confidence', 0.5)
        
        # Get the learned adjustment for this context
        confidence_delta, stability_factor = rl_core.learning_store.get_adjustment_for_context(
            country, domain, procedure_id
        )
        
        # Apply the adjustment to the original confidence
        adjusted_confidence = original_confidence + confidence_delta
        
        # Bound the result between 0 and 1
        bounded_confidence = max(0.0, min(1.0, adjusted_confidence))
        
        return bounded_confidence