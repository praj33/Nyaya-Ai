"""
Governed Execution Pipeline
Ensures all agent execution passes through enforcement controls
"""
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import traceback
from ..enforcement_engine.engine import (
    SovereignEnforcementEngine, 
    EnforcementSignal,
    EnforcementDecision
)
from ..enforcement_engine.decision_model import EnforcementResult


class GovernedExecutionPipeline:
    """Pipeline that governs all agent execution through enforcement controls"""
    
    def __init__(self):
        self.enforcement_engine = SovereignEnforcementEngine()
        self.pipeline_active = True
    
    def execute_with_governance(
        self, 
        agent_executor: Callable, 
        execution_context: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """
        Execute agent with full governance controls
        """
        try:
            # Create enforcement signal from execution context
            signal = self._create_enforcement_signal(execution_context, trace_id)
            
            # Check if execution is permitted
            if not self.enforcement_engine.is_execution_allowed(signal):
                # Execution blocked - return governed response
                return self.enforcement_engine.get_enforcement_response(signal)
            
            # Proceed with execution
            enforcement_result = self.enforcement_engine.make_enforcement_decision(signal)
            
            # Execute the actual agent function
            result = agent_executor(execution_context)
            
            # Add enforcement metadata to result
            if isinstance(result, dict):
                result['enforcement_metadata'] = {
                    'decision': enforcement_result.decision.value,
                    'rule_id': enforcement_result.rule_id,
                    'policy_source': enforcement_result.policy_source.value,
                    'governance_approved': True
                }
                result['trace_proof'] = self.enforcement_engine.signer.create_enforcement_proof(enforcement_result)
            else:
                result = {
                    'result': result,
                    'enforcement_metadata': {
                        'decision': enforcement_result.decision.value,
                        'rule_id': enforcement_result.rule_id,
                        'policy_source': enforcement_result.policy_source.value,
                        'governance_approved': True
                    },
                    'trace_proof': self.enforcement_engine.signer.create_enforcement_proof(enforcement_result)
                }
            
            return result
            
        except Exception as e:
            # On any exception, escalate to enforcement
            escalation_signal = self._create_escalation_signal(execution_context, trace_id, str(e))
            escalation_result = self.enforcement_engine.make_enforcement_decision(escalation_signal)
            
            return {
                "status": "error",
                "error_type": "execution_error",
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "trace_proof": self.enforcement_engine.signer.create_enforcement_proof(escalation_result),
                "enforcement_metadata": {
                    "decision": escalation_result.decision.value,
                    "rule_id": escalation_result.rule_id,
                    "policy_source": escalation_result.policy_source.value,
                    "governance_action": "error_handling"
                }
            }
    
    def _create_enforcement_signal(self, context: Dict[str, Any], trace_id: str) -> EnforcementSignal:
        """Create an enforcement signal from execution context"""
        return EnforcementSignal(
            case_id=context.get('case_id', 'unknown'),
            country=context.get('country', 'unknown'),
            domain=context.get('domain', 'general'),
            procedure_id=context.get('procedure_id', 'unknown'),
            original_confidence=context.get('original_confidence', 0.5),
            user_request=context.get('user_request', ''),
            jurisdiction_routed_to=context.get('jurisdiction_routed_to', 'unknown'),
            trace_id=trace_id,
            user_feedback=context.get('user_feedback'),
            outcome_tag=context.get('outcome_tag'),
            timestamp=datetime.utcnow()
        )
    
    def _create_escalation_signal(self, context: Dict[str, Any], trace_id: str, error_msg: str) -> EnforcementSignal:
        """Create an escalation signal for error situations"""
        return EnforcementSignal(
            case_id=context.get('case_id', 'unknown'),
            country=context.get('country', 'unknown'),
            domain=context.get('domain', 'general'),
            procedure_id=context.get('procedure_id', 'unknown'),
            original_confidence=context.get('original_confidence', 0.5),
            user_request=context.get('user_request', ''),
            jurisdiction_routed_to=context.get('jurisdiction_routed_to', 'unknown'),
            trace_id=trace_id,
            user_feedback=context.get('user_feedback'),
            outcome_tag='error',
            timestamp=datetime.utcnow()
        )
    
    def update_rl_with_governance(self, rl_update_func: Callable, signal_data: Dict[str, Any], trace_id: str) -> bool:
        """Update RL system with governance controls"""
        try:
            # Create signal for RL update
            signal = self._create_enforcement_signal(signal_data, trace_id)
            
            # Check if RL update is permitted
            if self.enforcement_engine.enforce_rl_learning(signal):
                # Execute RL update
                rl_update_func(signal_data)
                return True
            else:
                # RL update blocked
                return False
        except Exception:
            # On error, block the RL update
            return False
    
    def execute_fallback_with_governance(
        self, 
        fallback_executor: Callable, 
        fallback_context: Dict[str, Any],
        trace_id: str
    ) -> Dict[str, Any]:
        """Execute fallback procedures with governance"""
        # Create signal for fallback
        signal = self._create_enforcement_signal(fallback_context, trace_id)
        
        # Check if fallback is allowed
        if not self.enforcement_engine.is_execution_allowed(signal):
            # Return governed response for blocked fallback
            return self.enforcement_engine.get_enforcement_response(signal)
        
        # Execute fallback
        try:
            result = fallback_executor(fallback_context)
            enforcement_result = self.enforcement_engine.make_enforcement_decision(signal)
            
            if isinstance(result, dict):
                result['enforcement_metadata'] = {
                    'decision': enforcement_result.decision.value,
                    'rule_id': enforcement_result.rule_id,
                    'policy_source': enforcement_result.policy_source.value,
                    'governance_approved': True
                }
                result['trace_proof'] = self.enforcement_engine.signer.create_enforcement_proof(enforcement_result)
            else:
                result = {
                    'result': result,
                    'enforcement_metadata': {
                        'decision': enforcement_result.decision.value,
                        'rule_id': enforcement_result.rule_id,
                        'policy_source': enforcement_result.policy_source.value,
                        'governance_approved': True
                    },
                    'trace_proof': self.enforcement_engine.signer.create_enforcement_proof(enforcement_result)
                }
            
            return result
        except Exception as e:
            # Handle fallback execution error
            escalation_signal = self._create_escalation_signal(fallback_context, trace_id, str(e))
            escalation_result = self.enforcement_engine.make_enforcement_decision(escalation_signal)
            
            return {
                "status": "error",
                "error_type": "fallback_error",
                "error_message": str(e),
                "trace_proof": self.enforcement_engine.signer.create_enforcement_proof(escalation_result),
                "enforcement_metadata": {
                    "decision": escalation_result.decision.value,
                    "rule_id": escalation_result.rule_id,
                    "policy_source": escalation_result.policy_source.value,
                    "governance_action": "fallback_error_handling"
                }
            }


# Global pipeline instance
governed_pipeline = GovernedExecutionPipeline()


def execute_governed_agent(agent_executor: Callable, context: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """Global function to execute an agent with governance"""
    return governed_pipeline.execute_with_governance(agent_executor, context, trace_id)


def execute_governed_fallback(fallback_executor: Callable, context: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """Global function to execute a fallback with governance"""
    return governed_pipeline.execute_fallback_with_governance(fallback_executor, context, trace_id)


def update_rl_governed(rl_update_func: Callable, signal_data: Dict[str, Any], trace_id: str) -> bool:
    """Global function to update RL with governance"""
    return governed_pipeline.update_rl_with_governance(rl_update_func, signal_data, trace_id)