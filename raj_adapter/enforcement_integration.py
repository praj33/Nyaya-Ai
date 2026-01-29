"""
Raj's Schema Integration with Enforcement Engine
Integrates Raj's procedural intelligence with the sovereign enforcement engine
"""
from typing import Dict, Any
from .schema_consumer import (
    RajSchemaConsumer, 
    FailurePath, 
    EvidenceReadiness, 
    SystemCompliance,
    get_raj_consumer
)

# Import EnforcementDecision, DecisionContext, EnforcementRule, and PolicySource inside class methods to avoid circular imports
def _get_enforcement_classes():
    from enforcement_engine.decision_model import EnforcementDecision, DecisionContext
    from enforcement_engine.rules import EnforcementRule, PolicySource
    return EnforcementDecision, DecisionContext, EnforcementRule, PolicySource


class RajFailurePathRule:
    """Rule that enforces Raj's failure path schemas"""
    
    def __init__(self, raj_consumer: RajSchemaConsumer):
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        
        self.rule_id = "RAJ-FAILURE-001"
        self.policy_source = PolicySource.COMPLIANCE
        self.description = "Enforces Raj's failure path schemas to prevent known failure modes"
        self.raj_consumer = raj_consumer
    
    def evaluate(self, context):
        """Evaluate using Raj's failure path schemas"""
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        
        # Check if the context matches any known failure paths
        case_context = {
            'country': context.country,
            'domain': context.domain,
            'procedure_id': context.procedure_id,
            'original_confidence': context.original_confidence,
            'user_request': context.user_request
        }
        
        relevant_paths = self.raj_consumer.find_relevant_failure_paths(case_context)
        
        for path in relevant_paths:
            # If escalation is required for this failure path, escalate
            if path.escalation_required:
                return EnforcementDecision.ESCALATE
        
        # If no problematic failure paths are triggered, allow
        return EnforcementDecision.ALLOW


class RajEvidenceReadinessRule:
    """Rule that enforces Raj's evidence readiness schemas"""
    
    def __init__(self, raj_consumer: RajSchemaConsumer):
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        
        self.rule_id = "RAJ-EVIDENCE-001"
        self.policy_source = PolicySource.COMPLIANCE
        self.description = "Enforces Raj's evidence readiness schemas before proceeding"
        self.raj_consumer = raj_consumer
    
    def evaluate(self, context):
        """Evaluate using Raj's evidence readiness schemas"""
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        
        # For now, assume we're checking evidence readiness based on domain
        readiness_check = self.raj_consumer.check_evidence_readiness(
            context.domain,
            []  # In a real implementation, we'd have actual evidence to check
        )
        
        if not readiness_check['ready']:
            # If evidence is not ready, decide based on severity
            if readiness_check['blocking_issues']:
                return EnforcementDecision.BLOCK
            elif readiness_check['readiness_score'] < 0.3:
                return EnforcementDecision.ESCALATE
            else:
                return EnforcementDecision.SOFT_REDIRECT
        
        return EnforcementDecision.ALLOW


class RajComplianceRule:
    """Rule that enforces Raj's system compliance schemas"""
    
    def __init__(self, raj_consumer: RajSchemaConsumer):
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        
        self.rule_id = "RAJ-COMPLIANCE-001"
        self.policy_source = PolicySource.COMPLIANCE
        self.description = "Enforces Raj's system compliance rules"
        self.raj_consumer = raj_consumer
    
    def evaluate(self, context):
        """Evaluate using Raj's compliance schemas"""
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        
        # Check general compliance rules
        # This would typically check various compliance aspects based on context
        
        # For now, check if jurisdiction routing is compliant
        if context.country != context.jurisdiction_routed_to:
            compliance_check = self.raj_consumer.validate_system_compliance(
                "SC_LEGAL_001",  # Jurisdiction-specific legal advice rule
                {
                    'source_country': context.country,
                    'routed_to': context.jurisdiction_routed_to
                }
            )
            
            if not compliance_check['compliant']:
                return EnforcementDecision.BLOCK
        
        return EnforcementDecision.ALLOW


class RajEnforcementIntegrator:
    """Integrator that connects Raj's schemas to the enforcement engine"""
    
    def __init__(self):
        self.raj_consumer = get_raj_consumer()
        self.raj_rules = [
            RajFailurePathRule(self.raj_consumer),
            RajEvidenceReadinessRule(self.raj_consumer),
            RajComplianceRule(self.raj_consumer)
        ]
    
    def get_raj_rules(self):
        """Get all Raj-integrated rules"""
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        return self.raj_rules
    
    def validate_against_raj_schemas(self, context):
        """Perform comprehensive validation against Raj's schemas"""
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        
        validation_results = {
            'failure_paths_check': self._check_failure_paths(context),
            'evidence_readiness_check': self._check_evidence_readiness(context),
            'compliance_check': self._check_compliance(context)
        }
        
        return validation_results
    
    def _check_failure_paths(self, context):
        """Check against Raj's failure paths"""
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        
        case_context = {
            'country': context.country,
            'domain': context.domain,
            'procedure_id': context.procedure_id,
            'original_confidence': context.original_confidence,
            'user_request': context.user_request
        }
        
        relevant_paths = self.raj_consumer.find_relevant_failure_paths(case_context)
        
        return {
            'relevant_paths': [path.path_id for path in relevant_paths],
            'escalation_required': any(path.escalation_required for path in relevant_paths),
            'count': len(relevant_paths)
        }
    
    def _check_evidence_readiness(self, context):
        """Check evidence readiness using Raj's schemas"""
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        
        readiness_result = self.raj_consumer.check_evidence_readiness(
            context.domain,
            []  # Would have actual evidence in real implementation
        )
        
        return readiness_result
    
    def _check_compliance(self, context):
        """Check compliance using Raj's schemas"""
        # Import classes here to avoid circular import
        EnforcementDecision, DecisionContext, EnforcementRule, PolicySource = _get_enforcement_classes()
        
        compliance_results = []
        
        # Check jurisdiction compliance
        jurisdiction_check = self.raj_consumer.validate_system_compliance(
            "SC_LEGAL_001",
            {
                'source_country': context.country,
                'routed_to': context.jurisdiction_routed_to
            }
        )
        compliance_results.append(jurisdiction_check)
        
        return {
            'checks_performed': compliance_results,
            'all_compliant': all(check.get('compliant', True) for check in compliance_results)
        }


_raj_enforcement_integrator_instance = None


def get_raj_enforcement_integrator():
    """Get the global Raj enforcement integrator instance"""
    global _raj_enforcement_integrator_instance
    if _raj_enforcement_integrator_instance is None:
        _raj_enforcement_integrator_instance = RajEnforcementIntegrator()
    return _raj_enforcement_integrator_instance


def register_raj_rules_with_enforcement_engine():
    """Function to register Raj's rules with the enforcement engine"""
    from ..enforcement_engine.rules import EnforcementRuleEngine
    
    # This would be called to add Raj's rules to the main engine
    # In a real implementation, this would integrate with the existing rule engine
    integrator = get_raj_enforcement_integrator()
    raj_rules = integrator.get_raj_rules()
    
    # Return the rules so they can be added to the main engine
    return raj_rules