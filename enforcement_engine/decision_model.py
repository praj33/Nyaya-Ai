"""
Decision Model for Sovereign Enforcement Engine
Defines the core decision types and structures for enforcement decisions
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


class EnforcementDecision(Enum):
    ALLOW = "ALLOW"
    SOFT_REDIRECT = "SOFT_REDIRECT"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class PolicySource(Enum):
    CONSTITUTIONAL = "Constitutional"
    GOVERNANCE = "Governance"
    SYSTEM_SAFETY = "System Safety"
    COMPLIANCE = "Compliance"


@dataclass
class DecisionContext:
    """Context for making an enforcement decision"""
    case_id: str
    country: str
    domain: str
    procedure_id: str
    original_confidence: float
    user_request: str
    jurisdiction_routed_to: str
    trace_id: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class EnforcementResult:
    """Result of an enforcement decision"""
    decision: EnforcementDecision
    rule_id: str
    policy_source: PolicySource
    reasoning_summary: str
    trace_id: str
    timestamp: datetime
    signed_decision_object: Dict[str, Any]
    proof_hash: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "decision": self.decision.value,
            "rule_id": self.rule_id,
            "policy_source": self.policy_source.value,
            "reasoning_summary": self.reasoning_summary,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "signed_decision_object": self.signed_decision_object,
            "proof_hash": self.proof_hash,
            "metadata": self.metadata or {}
        }


@dataclass
class EnforcementSignal:
    """Signal passed to enforcement engine"""
    case_id: str
    country: str
    domain: str
    procedure_id: str
    original_confidence: float
    user_request: str
    jurisdiction_routed_to: str
    trace_id: str
    user_feedback: Optional[str] = None
    outcome_tag: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()