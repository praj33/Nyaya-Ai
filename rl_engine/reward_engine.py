"""
Reward & Penalty Engine for RL System
Implements bounded reward shaping based on feedback and outcomes
"""
from typing import Dict, Tuple


class RewardEngine:
    """Handles the computation of rewards and penalties based on signals"""
    
    def __init__(self):
        # Define reward/penalty magnitudes
        self.POSITIVE_FEEDBACK_REWARD = 0.1
        self.NEGATIVE_FEEDBACK_PENALTY = -0.15
        self.RESOLVED_OUTCOME_BONUS = 0.05
        self.WRONG_OUTCOME_PENALTY = -0.2
        self.ESCALATED_OUTCOME_PENALTY = -0.1
        self.PENDING_OUTCOME_NEUTRAL = 0.0
        
        # Maximum adjustment bounds
        self.MAX_CONFIDENCE_ADJUSTMENT = 0.3
        self.MIN_CONFIDENCE = 0.0
        self.MAX_CONFIDENCE = 1.0
    
    def compute_reward(self, signal: Dict) -> float:
        """
        Compute reward based on the learning signal
        Rules:
        - Positive feedback → confidence boost (upper-bounded)
        - Negative feedback → confidence decay
        - Wrong outcome → strong penalty
        - Repeated success → reduced volatility (stabilization)
        - Neutral feedback → no change
        """
        reward = 0.0
        
        # Process user feedback
        user_feedback = signal.get('user_feedback', 'neutral')
        if user_feedback == 'positive':
            reward += self.POSITIVE_FEEDBACK_REWARD
        elif user_feedback == 'negative':
            reward += self.NEGATIVE_FEEDBACK_PENALTY
        # neutral feedback adds nothing
        
        # Process outcome tag
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
        
        return reward
    
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
    
    def get_confidence_delta(self, original_confidence: float, signal: Dict, stability_factor: float = 0.1) -> float:
        """
        Get the delta that should be applied to the confidence
        """
        new_confidence = self.compute_adjusted_confidence(original_confidence, signal, stability_factor)
        return new_confidence - original_confidence