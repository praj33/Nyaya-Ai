"""
Reward & Penalty Engine for RL System
Implements bounded reward shaping based on feedback and outcomes
"""
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta


class RewardEngine:
    """Handles the computation of rewards and penalties based on signals with hardening"""
    
    def __init__(self):
        # Define reward/penalty magnitudes
        self.POSITIVE_FEEDBACK_REWARD = 0.05  # Reduced from 0.1 for stability
        self.NEGATIVE_FEEDBACK_PENALTY = -0.08  # Reduced from -0.15 for stability
        self.RESOLVED_OUTCOME_BONUS = 0.03  # Reduced from 0.05 for stability
        self.WRONG_OUTCOME_PENALTY = -0.15  # Reduced from -0.2 for stability
        self.ESCALATED_OUTCOME_PENALTY = -0.05  # Reduced from -0.1 for stability
        self.PENDING_OUTCOME_NEUTRAL = 0.0
        
        # Maximum adjustment bounds (stricter)
        self.MAX_CONFIDENCE_ADJUSTMENT = 0.15  # Reduced from 0.3 for stability
        self.MIN_CONFIDENCE = 0.0
        self.MAX_CONFIDENCE = 1.0
        
        # Hardening parameters
        self.MAX_DELTA_PER_UPDATE = 0.03  # Absolute cap on confidence change per update
        self.VOLATILITY_CAP = 0.02  # Maximum variance allowed in confidence adjustments
        
        # Anomaly detection thresholds
        self.ANOMALY_FEEDBACK_THRESHOLD = 5  # Max feedbacks from same user in time window
        self.ANOMALY_TIME_WINDOW = timedelta(hours=1)  # Time window for anomaly detection
        self.EXTREME_FEEDBACK_THRESHOLD = 0.8  # Feedback values beyond this are considered extreme
    
    def is_anomalous_signal(self, signal: Dict, recent_feedback_history: list) -> Tuple[bool, str]:
        """
        Detect anomalous signals that should be rejected
        Returns (is_anomalous, reason)
        """
        # Check for extreme feedback values
        user_feedback = signal.get('user_feedback', 'neutral')
        if user_feedback in ['positive', 'negative']:
            # Convert feedback to numeric for extreme checking
            feedback_score = 1.0 if user_feedback == 'positive' else -1.0
            if abs(feedback_score) >= self.EXTREME_FEEDBACK_THRESHOLD:
                return True, "extreme_feedback_value"
        
        # Check for repeated feedback from same user
        user_id = signal.get('user_id', 'unknown')
        current_time = datetime.fromisoformat(signal.get('timestamp', datetime.utcnow().isoformat()))
        
        recent_user_feedbacks = [
            f for f in recent_feedback_history 
            if f.get('user_id') == user_id and 
            datetime.fromisoformat(f.get('timestamp', datetime.utcnow().isoformat())) > 
            current_time - self.ANOMALY_TIME_WINDOW
        ]
        
        if len(recent_user_feedbacks) >= self.ANOMALY_FEEDBACK_THRESHOLD:
            return True, "repeated_feedback_from_user"
        
        # Check for outcome validity (Raj's validation)
        outcome_valid = signal.get('outcome_valid', True)  # From Raj's validation
        if not outcome_valid:
            return True, "invalid_outcome_from_raj"
        
        return False, ""
    
    def compute_reward(self, signal: Dict, recent_feedback_history: list = None) -> Tuple[float, bool, str]:
        """
        Compute reward based on the learning signal with hardening
        Returns (reward, should_learn, rejection_reason)
        Rules:
        - Raj's validation always dominates
        - Positive feedback → confidence boost (upper-bounded)
        - Negative feedback → confidence decay
        - Wrong outcome → strong penalty
        - Repeated success → reduced volatility (stabilization)
        - Neutral feedback → no change
        - Anomalous signals are rejected
        """
        # First check if we should learn at all
        outcome_valid = signal.get('outcome_valid', True)
        if not outcome_valid:
            return 0.0, False, "raj_validation_invalid"
        
        # Check for anomalous signals
        if recent_feedback_history:
            is_anomalous, reason = self.is_anomalous_signal(signal, recent_feedback_history)
            if is_anomalous:
                return 0.0, False, reason
        
        reward = 0.0
        
        # Process user feedback (secondary weight)
        user_feedback = signal.get('user_feedback', 'neutral')
        if user_feedback == 'positive':
            reward += self.POSITIVE_FEEDBACK_REWARD
        elif user_feedback == 'negative':
            reward += self.NEGATIVE_FEEDBACK_PENALTY
        # neutral feedback adds nothing
        
        # Process outcome tag (primary weight)
        outcome_tag = signal.get('outcome_tag', 'pending')
        if outcome_tag == 'resolved':
            reward += self.RESOLVED_OUTCOME_BONUS
        elif outcome_tag == 'wrong':
            reward += self.WRONG_OUTCOME_PENALTY
        elif outcome_tag == 'escalated':
            reward += self.ESCALATED_OUTCOME_PENALTY
        elif outcome_tag == 'pending':
            reward += self.PENDING_OUTCOME_NEUTRAL
        
        # Apply bounds to the reward
        reward = max(-self.MAX_CONFIDENCE_ADJUSTMENT, min(self.MAX_CONFIDENCE_ADJUSTMENT, reward))
        
        return reward, True, ""
    
    def apply_max_delta_protection(self, confidence_delta: float) -> float:
        """Apply absolute cap on confidence change per update"""
        return max(-self.MAX_DELTA_PER_UPDATE, min(self.MAX_DELTA_PER_UPDATE, confidence_delta))
    
    def apply_volatility_cap(self, confidence_delta: float, current_variance: float) -> float:
        """Apply volatility cap to prevent oscillation"""
        if current_variance > self.VOLATILITY_CAP:
            # Reduce the delta to bring variance back within bounds
            reduction_factor = self.VOLATILITY_CAP / current_variance
            return confidence_delta * reduction_factor
        return confidence_delta
    
    def adjust_for_confidence_level(self, reward: float, original_confidence: float) -> float:
        """
        Adjust reward based on the original confidence level
        Lower confidence inputs get amplified adjustments
        Higher confidence inputs get dampened adjustments
        """
        # Lower confidence predictions get slightly more adjustment
        confidence_factor = 1.0 - abs(original_confidence - 0.5)  # Near 0.5 gets more adjustment
        adjusted_reward = reward * (0.7 + 0.3 * confidence_factor)  # Range from 0.7x to 1.0x
        
        return max(-self.MAX_CONFIDENCE_ADJUSTMENT, min(self.MAX_CONFIDENCE_ADJUSTMENT, adjusted_reward))
    
    def apply_stability_factor(self, reward: float, stability_factor: float) -> float:
        """
        Apply stability factor to dampen adjustments for stable contexts
        Higher stability = less volatility in adjustments
        """
        # Stability factor reduces the magnitude of the reward/penalty
        # 0.1 = very unstable (high adjustment), 1.0 = very stable (low adjustment)
        adjusted_reward = reward * (1.0 - 0.7 * stability_factor)  # Even with max stability, some learning happens
        
        return adjusted_reward
    
    def compute_adjusted_confidence(self, original_confidence: float, signal: Dict, stability_factor: float = 0.1) -> float:
        """
        Compute the new confidence after applying reward adjustments
        """
        # Compute base reward
        base_reward = self.compute_reward(signal)
        
        # Adjust for original confidence level
        confidence_adjusted_reward = self.adjust_for_confidence_level(base_reward, original_confidence)
        
        # Apply stability factor
        final_adjustment = self.apply_stability_factor(confidence_adjusted_reward, stability_factor)
        
        # Calculate new confidence
        new_confidence = original_confidence + final_adjustment
        
        # Bound the confidence between MIN and MAX
        bounded_confidence = max(self.MIN_CONFIDENCE, min(self.MAX_CONFIDENCE, new_confidence))
        
        return bounded_confidence
    
    def get_confidence_delta(self, original_confidence: float, signal: Dict, stability_factor: float = 0.1, recent_feedback_history: list = None, current_variance: float = 0.0) -> Tuple[float, bool, str]:
        """
        Get the delta that should be applied to the confidence with hardening
        Returns (delta, should_learn, rejection_reason)
        """
        # Compute base reward with anomaly detection
        base_reward, should_learn, rejection_reason = self.compute_reward(signal, recent_feedback_history)
        
        if not should_learn:
            return 0.0, False, rejection_reason
        
        # Adjust for original confidence level
        confidence_adjusted_reward = self.adjust_for_confidence_level(base_reward, original_confidence)
        
        # Apply stability factor
        final_adjustment = self.apply_stability_factor(confidence_adjusted_reward, stability_factor)
        
        # Apply hardening protections
        final_adjustment = self.apply_max_delta_protection(final_adjustment)
        final_adjustment = self.apply_volatility_cap(final_adjustment, current_variance)
        
        return final_adjustment, True, ""