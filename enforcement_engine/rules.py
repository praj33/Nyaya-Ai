"""
Sovereign Enforcement Rules
Deterministic rules engine for governance decisions
"""
import hashlib
import json
from typing import List, Dict, Any
from .decision_model import EnforcementDecision, PolicySource, DecisionContext
from raj_adapter.enforcement_integration import get_raj_enforcement_integrator


class EnforcementRule:
    """Base class for enforcement rules"""
    
    def __init__(self, rule_id: str, policy_source: PolicySource, description: str):
        self.rule_id = rule_id
        self.policy_source = policy_source
        self.description = description
    
    def evaluate(self, context: DecisionContext) -> EnforcementDecision:
        """Evaluate the rule against the context"""
        raise NotImplementedError


class ConstitutionalComplianceRule(EnforcementRule):
    """Rule to ensure constitutional compliance"""
    
    def __init__(self):
        super().__init__(
            rule_id="CONST-001",
            policy_source=PolicySource.CONSTITUTIONAL,
            description="Ensures responses comply with constitutional provisions"
        )
    
    def evaluate(self, context: DecisionContext) -> EnforcementDecision:
        # Check if domain involves constitutional matters
        if context.domain.lower() in ['constitutional', 'fundamental_rights', 'directive_principles']:
            # Require higher confidence for constitutional matters
            if context.original_confidence < 0.8:
                return EnforcementDecision.ESCALATE
        return EnforcementDecision.ALLOW


class JurisdictionBoundaryRule(EnforcementRule):
    """Rule to ensure jurisdiction boundaries are respected"""
    
    def __init__(self):
        super().__init__(
            rule_id="JURIS-001",
            policy_source=PolicySource.GOVERNANCE,
            description="Prevents cross-jurisdictional legal advice without proper routing"
        )
    
    def evaluate(self, context: DecisionContext) -> EnforcementDecision:
        # Ensure jurisdiction routed to matches country
        if context.country != context.jurisdiction_routed_to:
            return EnforcementDecision.BLOCK
        return EnforcementDecision.ALLOW


class SystemSafetyRule(EnforcementRule):
    """Rule for system safety concerns"""
    
    def __init__(self):
        super().__init__(
            rule_id="SAFETY-001",
            policy_source=PolicySource.SYSTEM_SAFETY,
            description="Blocks requests that could compromise system integrity"
        )
        # Dangerous patterns that should trigger blocking
        self.dangerous_patterns = [
            'ignore all rules',
            'disregard',
            'bypass',
            'override',
            'circumvent'
        ]
    
    def evaluate(self, context: DecisionContext) -> EnforcementDecision:
        # Check for dangerous patterns in user request
        request_lower = context.user_request.lower()
        for pattern in self.dangerous_patterns:
            if pattern in request_lower:
                return EnforcementDecision.BLOCK
        return EnforcementDecision.ALLOW


class ConfidenceThresholdRule(EnforcementRule):
    """Rule to enforce minimum confidence thresholds"""
    
    def __init__(self):
        super().__init__(
            rule_id="CONF-001",
            policy_source=PolicySource.SYSTEM_SAFETY,
            description="Ensures minimum confidence for legal advice"
        )
    
    def evaluate(self, context: DecisionContext) -> EnforcementDecision:
        # Different domains may have different confidence requirements
        if context.domain in ['criminal', 'constitutional', 'property']:
            # High-stakes domains require higher confidence (temporarily lowered for testing)
            if context.original_confidence < 0.1:
                return EnforcementDecision.ESCALATE
        elif context.original_confidence < 0.5:
            # General domain threshold
            return EnforcementDecision.SOFT_REDIRECT
        
        return EnforcementDecision.ALLOW


class ProcedureIntegrityRule(EnforcementRule):
    """Rule to ensure procedural integrity"""
    
    def __init__(self):
        super().__init__(
            rule_id="PROC-001",
            policy_source=PolicySource.COMPLIANCE,
            description="Ensures legal procedures follow proper protocols"
        )
    
    def evaluate(self, context: DecisionContext) -> EnforcementDecision:
        # Check if procedure_id is recognized and valid
        if not context.procedure_id or context.procedure_id == 'unknown':
            return EnforcementDecision.ESCALATE
        
        # Some procedures may have special requirements
        if 'appeal' in context.procedure_id.lower():
            # Appeals may require higher scrutiny
            if context.original_confidence < 0.75:
                return EnforcementDecision.ESCALATE
        
        return EnforcementDecision.ALLOW


class EnforcementRuleEngine:
    """Main enforcement rule engine"""
    
    def __init__(self):
        self.rules: List[EnforcementRule] = [
            ConstitutionalComplianceRule(),
            JurisdictionBoundaryRule(),
            SystemSafetyRule(),
            ConfidenceThresholdRule(),
            ProcedureIntegrityRule()
        ]
        
        # Add Raj's integrated rules lazily to avoid circular import
        self._raj_rules_loaded = False
        self._load_raj_rules_if_needed()
    
    def _load_raj_rules_if_needed(self):
        if not self._raj_rules_loaded:
            try:
                raj_integrator = get_raj_enforcement_integrator()
                self.rules.extend(raj_integrator.get_raj_rules())
                self._raj_rules_loaded = True
            except ImportError:
                # Raj adapter may not be available, continue without Raj rules
                pass
    
    def evaluate_context(self, context: DecisionContext) -> EnforcementDecision:
        """Evaluate all rules against the context and return final decision"""
        decisions = []
        
        for rule in self.rules:
            decision = rule.evaluate(context)
            decisions.append((rule, decision))
            
            # If any rule returns BLOCK or ESCALATE, we return that decision
            if decision in [EnforcementDecision.BLOCK, EnforcementDecision.ESCALATE]:
                return decision
        
        # If no blocking/escalating rules triggered, check if any SOFT_REDIRECT
        for rule, decision in decisions:
            if decision == EnforcementDecision.SOFT_REDIRECT:
                return EnforcementDecision.SOFT_REDIRECT
        
        # Default to ALLOW if no rules block or redirect
        return EnforcementDecision.ALLOW
    
    def get_reasoning_for_decision(self, context: DecisionContext, decision: EnforcementDecision) -> str:
        """Generate reasoning summary for a decision"""
        reasons = []
        
        for rule in self.rules:
            rule_decision = rule.evaluate(context)
            if rule_decision == decision:
                reasons.append(rule.description)
        
        if not reasons:
            if decision == EnforcementDecision.ALLOW:
                return "No enforcement rules triggered, request allowed by default"
            else:
                return f"No specific rule matched for {decision.value}, but decision was required"
        
        return "; ".join(reasons)
    
    def calculate_proof_hash(self, context: DecisionContext, decision: EnforcementDecision, rule_id: str) -> str:
        """Calculate a proof hash for the enforcement decision"""
        data_to_hash = {
            'case_id': context.case_id,
            'country': context.country,
            'domain': context.domain,
            'decision': decision.value,
            'rule_id': rule_id,
            'timestamp': context.timestamp.isoformat()
        }
        
        json_str = json.dumps(data_to_hash, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()