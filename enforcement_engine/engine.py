"""
Sovereign Enforcement Engine
Deterministic governance layer that decides if Nyaya may proceed with requests
"""
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from .decision_model import (
    EnforcementDecision, PolicySource, DecisionContext, 
    EnforcementResult, EnforcementSignal
)
from .rules import EnforcementRuleEngine
from .signer import EnforcementSigner


class SovereignEnforcementEngine:
    """Main enforcement engine singleton"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SovereignEnforcementEngine, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.rule_engine = EnforcementRuleEngine()
        self.signer = EnforcementSigner()
        self._initialized = True
        self._thread_lock = threading.Lock()
    
    def make_enforcement_decision(self, signal: EnforcementSignal) -> EnforcementResult:
        """Make an enforcement decision based on the signal"""
        with self._thread_lock:
            # Create decision context from signal
            context = DecisionContext(
                case_id=signal.case_id,
                country=signal.country,
                domain=signal.domain,
                procedure_id=signal.procedure_id,
                original_confidence=signal.original_confidence,
                user_request=signal.user_request,
                jurisdiction_routed_to=signal.jurisdiction_routed_to,
                trace_id=signal.trace_id,
                timestamp=signal.timestamp
            )
            
            # Evaluate the context using the rule engine
            decision = self.rule_engine.evaluate_context(context)
            
            # Find the rule that caused the decision (for rule_id)
            rule_id = self._get_applicable_rule_id(context, decision)
            
            # Generate reasoning summary
            reasoning_summary = self.rule_engine.get_reasoning_for_decision(context, decision)
            
            # Calculate proof hash
            proof_hash = self.rule_engine.calculate_proof_hash(context, decision, rule_id)
            
            # Create signed decision object
            unsigned_result = EnforcementResult(
                decision=decision,
                rule_id=rule_id,
                policy_source=PolicySource.GOVERNANCE,  # Default policy source
                reasoning_summary=reasoning_summary,
                trace_id=context.trace_id,
                timestamp=context.timestamp,
                signed_decision_object={},
                proof_hash=proof_hash
            )
            
            # Create the signed decision object
            signed_decision_obj = self.signer.create_signed_decision_object(unsigned_result)
            
            # Create final result with signed object
            result = EnforcementResult(
                decision=decision,
                rule_id=rule_id,
                policy_source=self._get_policy_source_for_decision(decision),
                reasoning_summary=reasoning_summary,
                trace_id=context.trace_id,
                timestamp=context.timestamp,
                signed_decision_object=signed_decision_obj,
                proof_hash=proof_hash
            )
            
            return result
    
    def _get_applicable_rule_id(self, context: DecisionContext, decision: EnforcementDecision) -> str:
        """Get the rule ID that led to this decision"""
        for rule in self.rule_engine.rules:
            rule_decision = rule.evaluate(context)
            if rule_decision == decision:
                return rule.rule_id
        # If no specific rule matched, return a default
        return f"DEFAULT-{decision.value}"
    
    def _get_policy_source_for_decision(self, decision: EnforcementDecision) -> PolicySource:
        """Determine the appropriate policy source for a decision"""
        if decision in [EnforcementDecision.BLOCK, EnforcementDecision.ESCALATE]:
            return PolicySource.SYSTEM_SAFETY
        else:
            return PolicySource.GOVERNANCE
    
    def is_execution_allowed(self, signal: EnforcementSignal) -> bool:
        """Check if execution is allowed based on enforcement decision"""
        result = self.make_enforcement_decision(signal)
        return result.decision in [EnforcementDecision.ALLOW, EnforcementDecision.SOFT_REDIRECT]
    
    def get_governed_response(self, signal: EnforcementSignal) -> Dict[str, Any]:
        """Get a governed response that includes enforcement proof"""
        result = self.make_enforcement_decision(signal)
        
        if result.decision in [EnforcementDecision.ALLOW, EnforcementDecision.SOFT_REDIRECT]:
            # Execution is allowed, return success response with proof
            return {
                "status": "allowed",
                "decision": result.decision.value,
                "trace_proof": self.signer.create_enforcement_proof(result),
                "enforcement_metadata": {
                    "rule_id": result.rule_id,
                    "policy_source": result.policy_source.value,
                    "reasoning": result.reasoning_summary
                }
            }
        else:
            # Execution is blocked, return blocked response
            return {
                "status": "blocked",
                "reason": "governance enforced",
                "decision": result.decision.value,
                "trace_proof": self.signer.create_enforcement_proof(result),
                "enforcement_metadata": {
                    "rule_id": result.rule_id,
                    "policy_source": result.policy_source.value,
                    "reasoning": result.reasoning_summary
                }
            }
    
    def enforce_rl_update(self, signal: EnforcementSignal) -> bool:
        """Enforce whether RL updates are allowed"""
        # For RL updates, we may have different rules
        # For now, allow RL updates unless specifically blocked by safety rules
        context = DecisionContext(
            case_id=signal.case_id,
            country=signal.country,
            domain=signal.domain,
            procedure_id=signal.procedure_id,
            original_confidence=signal.original_confidence,
            user_request=signal.user_request,
            jurisdiction_routed_to=signal.jurisdiction_routed_to,
            trace_id=signal.trace_id,
            timestamp=signal.timestamp
        )
        
        # Check specifically for safety rules that might block learning
        for rule in self.rule_engine.rules:
            if isinstance(rule, (EnforcementRule)):
                decision = rule.evaluate(context)
                if decision == EnforcementDecision.BLOCK:
                    # Check if this is a safety/system integrity rule
                    if rule.policy_source in [PolicySource.SYSTEM_SAFETY]:
                        return False
        
        return True


# Global functions for external use
def enforce_request(signal: EnforcementSignal) -> EnforcementResult:
    """Global function to enforce a request"""
    engine = SovereignEnforcementEngine()
    return engine.make_enforcement_decision(signal)


def is_execution_permitted(signal: EnforcementSignal) -> bool:
    """Global function to check if execution is permitted"""
    engine = SovereignEnforcementEngine()
    return engine.is_execution_allowed(signal)


def get_enforcement_response(signal: EnforcementSignal) -> Dict[str, Any]:
    """Global function to get a governed response"""
    engine = SovereignEnforcementEngine()
    return engine.get_governed_response(signal)


def enforce_rl_learning(signal: EnforcementSignal) -> bool:
    """Global function to enforce RL learning updates"""
    engine = SovereignEnforcementEngine()
    return engine.enforce_rl_update(signal)