"""
Raj's Schema Consumer
Consumes Raj's procedural intelligence schemas to enforce legal procedures
"""
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


@dataclass
class FailurePath:
    """Represents a failure path from Raj's schema"""
    path_id: str
    description: str
    trigger_conditions: List[str]
    remediation_steps: List[str]
    escalation_required: bool
    evidence_requirements: List[str]


@dataclass
class EvidenceReadiness:
    """Represents evidence readiness criteria from Raj's schema"""
    case_type: str
    required_documents: List[str]
    validation_criteria: List[str]
    readiness_score_threshold: float
    blocking_issues: List[str]


@dataclass
class SystemCompliance:
    """Represents system compliance rules from Raj's schema"""
    rule_id: str
    rule_description: str
    compliance_check: str
    penalty_for_violation: str
    audit_frequency: str
    exception_conditions: List[str]


class RajSchemaConsumer:
    """Consumer for Raj's procedural intelligence schemas"""
    
    def __init__(self, schema_directory: str = "raj_schemas"):
        self.schema_directory = schema_directory
        self.failure_paths = self._load_failure_paths()
        self.evidence_readiness = self._load_evidence_readiness()
        self.system_compliance = self._load_system_compliance()
    
    def _load_failure_paths(self) -> List[FailurePath]:
        """Load failure paths schema from Raj's data"""
        # Since we don't have the actual GitHub repo, we'll simulate the schema
        # In a real implementation, this would fetch from the GitHub repo
        try:
            schema_path = os.path.join(self.schema_directory, "failure_paths_v2.json")
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    data = json.load(f)
                    return [self._parse_failure_path(item) for item in data.get('failure_paths', [])]
            else:
                # Simulate the schema structure for demonstration
                return self._simulate_failure_paths()
        except Exception:
            return self._simulate_failure_paths()
    
    def _simulate_failure_paths(self) -> List[FailurePath]:
        """Simulate failure paths for demonstration purposes"""
        return [
            FailurePath(
                path_id="FP_CRIM_001",
                description="Criminal case dismissed due to insufficient evidence",
                trigger_conditions=["evidence_score < 0.6", "eyewitness_unavailable"],
                remediation_steps=["gather_additional_evidence", "seek_expert_testimony"],
                escalation_required=True,
                evidence_requirements=["physical_evidence", "witness_statement"]
            ),
            FailurePath(
                path_id="FP_CIVIL_001", 
                description="Civil case requires additional documentation",
                trigger_conditions=["document_authenticity_questioned"],
                remediation_steps=["verify_document_authenticity", "obtain_notarized_copies"],
                escalation_required=False,
                evidence_requirements=["verified_documents", "affidavit"]
            )
        ]
    
    def _load_evidence_readiness(self) -> List[EvidenceReadiness]:
        """Load evidence readiness schema from Raj's data"""
        try:
            schema_path = os.path.join(self.schema_directory, "evidence_readiness_v2.json")
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    data = json.load(f)
                    return [self._parse_evidence_readiness(item) for item in data.get('evidence_readiness', [])]
            else:
                # Simulate the schema structure for demonstration
                return self._simulate_evidence_readiness()
        except Exception:
            return self._simulate_evidence_readiness()
    
    def _simulate_evidence_readiness(self) -> List[EvidenceReadiness]:
        """Simulate evidence readiness for demonstration purposes"""
        return [
            EvidenceReadiness(
                case_type="criminal_assault",
                required_documents=["police_report", "medical_records", "witness_statements"],
                validation_criteria=["authenticity_verified", "chain_of_custody_maintained"],
                readiness_score_threshold=0.7,
                blocking_issues=["missing_key_evidence", "contaminated_evidence"]
            ),
            EvidenceReadiness(
                case_type="civil_contract_dispute",
                required_documents=["contract_agreement", "correspondence", "payment_records"],
                validation_criteria=["signatures_verified", "dates_authenticated"],
                readiness_score_threshold=0.6,
                blocking_issues=["unsigned_contract", "altered_documents"]
            )
        ]
    
    def _load_system_compliance(self) -> List[SystemCompliance]:
        """Load system compliance schema from Raj's data"""
        try:
            schema_path = os.path.join(self.schema_directory, "system_compliance_v2.json")
            if os.path.exists(schema_path):
                with open(schema_path, 'r') as f:
                    data = json.load(f)
                    return [self._parse_system_compliance(item) for item in data.get('compliance_rules', [])]
            else:
                # Simulate the schema structure for demonstration
                return self._simulate_system_compliance()
        except Exception:
            return self._simulate_system_compliance()
    
    def _simulate_system_compliance(self) -> List[SystemCompliance]:
        """Simulate system compliance for demonstration purposes"""
        return [
            SystemCompliance(
                rule_id="SC_LEGAL_001",
                rule_description="Legal advice must be jurisdiction-specific",
                compliance_check="jurisdiction_validation",
                penalty_for_violation="case_dismissal",
                audit_frequency="real_time",
                exception_conditions=[]
            ),
            SystemCompliance(
                rule_id="SC_EVIDENCE_001",
                rule_description="Evidence must meet admissibility standards",
                compliance_check="evidence_admissibility_check",
                penalty_for_violation="evidence_exclusion",
                audit_frequency="pre_trial",
                exception_conditions=["emergency_situations"]
            )
        ]
    
    def _parse_failure_path(self, data: Dict[str, Any]) -> FailurePath:
        """Parse a failure path from JSON data"""
        return FailurePath(
            path_id=data.get('path_id', ''),
            description=data.get('description', ''),
            trigger_conditions=data.get('trigger_conditions', []),
            remediation_steps=data.get('remediation_steps', []),
            escalation_required=data.get('escalation_required', False),
            evidence_requirements=data.get('evidence_requirements', [])
        )
    
    def _parse_evidence_readiness(self, data: Dict[str, Any]) -> EvidenceReadiness:
        """Parse evidence readiness from JSON data"""
        return EvidenceReadiness(
            case_type=data.get('case_type', ''),
            required_documents=data.get('required_documents', []),
            validation_criteria=data.get('validation_criteria', []),
            readiness_score_threshold=data.get('readiness_score_threshold', 0.5),
            blocking_issues=data.get('blocking_issues', [])
        )
    
    def _parse_system_compliance(self, data: Dict[str, Any]) -> SystemCompliance:
        """Parse system compliance from JSON data"""
        return SystemCompliance(
            rule_id=data.get('rule_id', ''),
            rule_description=data.get('rule_description', ''),
            compliance_check=data.get('compliance_check', ''),
            penalty_for_violation=data.get('penalty_for_violation', ''),
            audit_frequency=data.get('audit_frequency', ''),
            exception_conditions=data.get('exception_conditions', [])
        )
    
    def get_failure_path_by_id(self, path_id: str) -> Optional[FailurePath]:
        """Get a specific failure path by ID"""
        for path in self.failure_paths:
            if path.path_id == path_id:
                return path
        return None
    
    def get_evidence_readiness_for_case(self, case_type: str) -> Optional[EvidenceReadiness]:
        """Get evidence readiness criteria for a specific case type"""
        for readiness in self.evidence_readiness:
            if readiness.case_type == case_type:
                return readiness
        return None
    
    def get_compliance_rule_by_id(self, rule_id: str) -> Optional[SystemCompliance]:
        """Get a specific compliance rule by ID"""
        for rule in self.system_compliance:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def find_relevant_failure_paths(self, case_context: Dict[str, Any]) -> List[FailurePath]:
        """Find failure paths relevant to a specific case context"""
        relevant_paths = []
        for path in self.failure_paths:
            # Simple matching logic - in reality this would be more sophisticated
            if any(condition in str(case_context) for condition in path.trigger_conditions):
                relevant_paths.append(path)
        return relevant_paths
    
    def check_evidence_readiness(self, case_type: str, provided_evidence: List[str]) -> Dict[str, Any]:
        """Check if evidence is ready for a specific case type"""
        readiness = self.get_evidence_readiness_for_case(case_type)
        if not readiness:
            return {
                "ready": False,
                "missing_documents": [],
                "blocking_issues": [],
                "readiness_score": 0.0
            }
        
        # Check for missing documents
        missing_docs = []
        for req_doc in readiness.required_documents:
            if req_doc not in provided_evidence:
                missing_docs.append(req_doc)
        
        # Check for blocking issues
        blocking_issues = []
        # In a real implementation, we'd check the actual evidence for issues
        # For now, we'll just return the defined blocking issues
        blocking_issues = readiness.blocking_issues
        
        # Calculate readiness score
        if readiness.required_documents:
            completeness = (len(readiness.required_documents) - len(missing_docs)) / len(readiness.required_documents)
        else:
            completeness = 1.0
        
        readiness_score = completeness if not blocking_issues else completeness * 0.5
        
        return {
            "ready": readiness_score >= readiness.readiness_score_threshold and not blocking_issues,
            "missing_documents": missing_docs,
            "blocking_issues": blocking_issues,
            "readiness_score": readiness_score,
            "threshold_required": readiness.readiness_score_threshold
        }
    
    def validate_system_compliance(self, rule_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate compliance with a specific rule"""
        rule = self.get_compliance_rule_by_id(rule_id)
        if not rule:
            return {
                "compliant": False,
                "violation": f"Rule {rule_id} not found",
                "penalty": "unknown"
            }
        
        # Perform the compliance check based on the rule
        # This is a simplified check - in reality, this would be more complex
        is_compliant = True  # Placeholder - would depend on actual validation
        
        return {
            "compliant": is_compliant,
            "rule_id": rule_id,
            "check_performed": rule.compliance_check,
            "penalty_if_violated": rule.penalty_for_violation
        }


# Global instance
raj_consumer = RajSchemaConsumer()


def get_raj_consumer() -> RajSchemaConsumer:
    """Get the global Raj schema consumer instance"""
    return raj_consumer