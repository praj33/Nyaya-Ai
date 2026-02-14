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


class IntentClassificationRule(EnforcementRule):
    """Rule to classify user intent and map to enforcement decision"""
    
    def __init__(self):
        super().__init__(
            rule_id="INTENT-001",
            policy_source=PolicySource.GOVERNANCE,
            description="Classifies user intent and enforces appropriate decision"
        )
        self.malicious_patterns = [
            'how to get away', 'avoid punishment', 'evade', 'escape charges',
            'hide evidence', 'destroy evidence', 'fake', 'forge', 'bribe',
            'how to commit', 'best way to steal', 'without getting caught'
        ]
        self.informational_patterns = [
            'what is', 'what are', 'punishment for', 'penalty for', 'law on',
            'legal definition', 'explain', 'tell me about', 'information on',
            'sections apply', 'which law', 'is it illegal', 'is it legal'
        ]
        self.advisory_patterns = [
            'what can i do', 'what should i do', 'how to file', 'legal action',
            'my rights', 'can i sue', 'how to proceed', 'next steps',
            'what are my options', 'legal help', 'need help', 'happened to me'
        ]
    
    def evaluate(self, context: DecisionContext) -> EnforcementDecision:
        request_lower = context.user_request.lower()
        
        # Check malicious intent
        if any(pattern in request_lower for pattern in self.malicious_patterns):
            return EnforcementDecision.RESTRICT
        
        # Check informational intent
        if any(pattern in request_lower for pattern in self.informational_patterns):
            return EnforcementDecision.ALLOW_INFORMATIONAL
        
        # Check advisory intent
        if any(pattern in request_lower for pattern in self.advisory_patterns):
            return EnforcementDecision.ALLOW
        
        # Default to SAFE_REDIRECT for ambiguous queries
        return EnforcementDecision.SAFE_REDIRECT


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
                return EnforcementDecision.SAFE_REDIRECT
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
            return EnforcementDecision.RESTRICT
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
                return EnforcementDecision.RESTRICT
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
            # High-stakes domains require higher confidence
            if context.original_confidence < 0.3:
                return EnforcementDecision.SAFE_REDIRECT
        elif context.original_confidence < 0.2:
            # General domain threshold
            return EnforcementDecision.SAFE_REDIRECT
        
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
            return EnforcementDecision.SAFE_REDIRECT
        
        # Some procedures may have special requirements
        if 'appeal' in context.procedure_id.lower():
            # Appeals may require higher scrutiny
            if context.original_confidence < 0.75:
                return EnforcementDecision.SAFE_REDIRECT
        
        return EnforcementDecision.ALLOW


class EnforcementRuleEngine:
    """Main enforcement rule engine"""
    
    def __init__(self):
        self.rules: List[EnforcementRule] = [
            IntentClassificationRule(),
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
        intent_decision = None
        
        for rule in self.rules:
            decision = rule.evaluate(context)
            decisions.append((rule, decision))
            
            # Track intent classification decision separately
            if isinstance(rule, IntentClassificationRule):
                intent_decision = decision
            
            # If any rule returns RESTRICT, we return that decision immediately
            if decision == EnforcementDecision.RESTRICT:
                return decision
        
        # Prioritize intent classification decision if it's not ALLOW
        if intent_decision and intent_decision != EnforcementDecision.ALLOW:
            return intent_decision
        
        # Check for ALLOW_INFORMATIONAL
        for rule, decision in decisions:
            if decision == EnforcementDecision.ALLOW_INFORMATIONAL:
                return EnforcementDecision.ALLOW_INFORMATIONAL
        
        # Check for SAFE_REDIRECT
        for rule, decision in decisions:
            if decision == EnforcementDecision.SAFE_REDIRECT:
                return EnforcementDecision.SAFE_REDIRECT
        
        # Default to ALLOW if all other rules allow
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