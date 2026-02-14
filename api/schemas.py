from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum

class EnforcementDecision(str, Enum):
    ALLOW_INFORMATIONAL = "ALLOW_INFORMATIONAL"
    ALLOW = "ALLOW"
    SAFE_REDIRECT = "SAFE_REDIRECT"
    RESTRICT = "RESTRICT"

class UserRole(str, Enum):
    CITIZEN = "citizen"
    LAWYER = "lawyer"
    STUDENT = "student"

class DomainHint(str, Enum):
    CRIMINAL = "criminal"
    CIVIL = "civil"
    FAMILY = "family"
    COMMERCIAL = "commercial"
    CONSTITUTIONAL = "constitutional"

class JurisdictionHint(str, Enum):
    INDIA = "India"
    UK = "UK"
    UAE = "UAE"

class UserContext(BaseModel):
    role: UserRole
    confidence_required: bool = True

class QueryRequest(BaseModel):
    query: str = Field(..., description="Legal query text")
    jurisdiction_hint: Optional[JurisdictionHint] = None
    domain_hint: Optional[DomainHint] = None
    user_context: UserContext

class MultiJurisdictionRequest(BaseModel):
    query: str = Field(..., description="Legal query text")
    jurisdictions: List[JurisdictionHint] = Field(..., min_items=1, max_items=3)

class ExplanationLevel(str, Enum):
    BRIEF = "brief"
    DETAILED = "detailed"
    CONSTITUTIONAL = "constitutional"

class ExplainReasoningRequest(BaseModel):
    trace_id: str = Field(..., description="UUID trace identifier")
    explanation_level: ExplanationLevel

class FeedbackType(str, Enum):
    CLARITY = "clarity"
    CORRECTNESS = "correctness"
    USEFULNESS = "usefulness"

class FeedbackRequest(BaseModel):
    trace_id: str = Field(..., description="UUID trace identifier")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    feedback_type: FeedbackType
    comment: Optional[str] = Field(None, max_length=1000)

class StatuteSchema(BaseModel):
    act: str
    year: int
    section: str
    title: str

class CaseLawSchema(BaseModel):
    title: str
    court: str
    year: int
    principle: str

class ConfidenceSchema(BaseModel):
    overall: float = Field(..., ge=0.0, le=1.0)
    jurisdiction: float = Field(..., ge=0.0, le=1.0)
    domain: float = Field(..., ge=0.0, le=1.0)
    statute_match: float = Field(..., ge=0.0, le=1.0)
    procedural_match: float = Field(..., ge=0.0, le=1.0)

class NyayaResponse(BaseModel):
    domain: str
    domains: List[str] = []
    jurisdiction: str
    jurisdiction_detected: str
    jurisdiction_confidence: float = Field(..., ge=0.0, le=1.0)
    confidence: ConfidenceSchema
    legal_route: List[str]
    statutes: List[StatuteSchema] = []
    case_laws: List[CaseLawSchema] = []
    constitutional_articles: List[str] = []
    provenance_chain: List[Dict[str, Any]] = []
    reasoning_trace: Dict[str, Any] = {}
    trace_id: str
    enforcement_decision: EnforcementDecision = EnforcementDecision.ALLOW
    timeline: List[Dict[str, str]] = []
    glossary: List[Dict[str, str]] = []
    evidence_requirements: List[str] = []

class MultiJurisdictionResponse(BaseModel):
    comparative_analysis: Dict[str, NyayaResponse]
    confidence: float = Field(..., ge=0.0, le=1.0)
    trace_id: str

class ExplainReasoningResponse(BaseModel):
    trace_id: str
    explanation: Dict[str, Any]
    reasoning_tree: Dict[str, Any]
    constitutional_articles: List[str] = []

class FeedbackResponse(BaseModel):
    status: str
    trace_id: str
    message: str

class TraceResponse(BaseModel):
    trace_id: str
    event_chain: List[Dict[str, Any]]
    agent_routing_tree: Dict[str, Any]
    jurisdiction_hops: List[str]
    rl_reward_snapshot: Dict[str, Any]
    context_fingerprint: str
    nonce_verification: bool
    signature_verification: bool

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    trace_id: str

class ProcedureRequest(BaseModel):
    country: str = Field(..., description="Country code (e.g., india, uae, uk)")
    domain: str = Field(..., description="Legal domain (e.g., criminal, civil, family, consumer_commercial)")
    current_step: Optional[str] = Field(None, description="Current canonical step")

class EvidenceAssessmentRequest(BaseModel):
    canonical_step: str = Field(..., description="Canonical step name")
    available_documents: List[str] = Field(..., description="List of available documents")

class FailureAnalysisRequest(BaseModel):
    failure_code: str = Field(..., description="Failure code to analyze")

class ProcedureComparisonRequest(BaseModel):
    countries: List[str] = Field(..., min_items=2, max_items=4, description="Countries to compare")
    domain: str = Field(..., description="Legal domain to compare")

class ProcedureResponse(BaseModel):
    country: str
    domain: str
    procedure_overview: Dict[str, Any]
    steps: List[Dict[str, Any]]
    escalation_paths: List[Dict[str, Any]]
    current_step_analysis: Optional[Dict[str, Any]] = None

class EvidenceAssessmentResponse(BaseModel):
    evidence_state: str
    mandatory_documents: List[str]
    available_documents: List[str]
    missing_documents: List[str]
    confidence_penalty: float
    readiness_percentage: float

class FailureAnalysisResponse(BaseModel):
    failure_code: str
    failure_type: str
    description: str
    recoverable: bool
    severity: str

class ProcedureComparisonResponse(BaseModel):
    domain: str
    countries: List[str]
    procedures: Dict[str, Any]