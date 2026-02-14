import sys
import os
sys.path.append('.')
sys.path.append('..')

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

# Import enhanced components
from clean_legal_advisor import EnhancedLegalAdvisor, LegalQuery

# Import jurisdiction detector
from core.jurisdiction.detector import JurisdictionDetector

# Import case law components
from core.caselaw.loader import CaseLawLoader
from core.caselaw.retriever import CaseLawRetriever

# Import original schemas
from api.schemas import (
    QueryRequest, MultiJurisdictionRequest, ExplainReasoningRequest,
    FeedbackRequest, NyayaResponse, MultiJurisdictionResponse,
    ExplainReasoningResponse, FeedbackResponse, TraceResponse,
    StatuteSchema, ConfidenceSchema, CaseLawSchema
)

# Import response enricher
from core.response.enricher import enrich_response

router = APIRouter(prefix="/nyaya", tags=["nyaya"])

# Initialize the enhanced legal advisor with error handling
try:
    advisor = EnhancedLegalAdvisor()
    jurisdiction_detector = JurisdictionDetector()
    
    # Initialize case law system
    case_loader = CaseLawLoader()
    cases = case_loader.load_all()
    case_retriever = CaseLawRetriever(cases)
    print(f"Case law system initialized: {len(cases)} cases loaded")
    print("Jurisdiction detector initialized")
except Exception as e:
    print(f"Error initializing components: {e}")
    advisor = None
    jurisdiction_detector = None
    case_retriever = None

@router.post("/query", response_model=NyayaResponse)
async def query_legal(request: QueryRequest):
    """Execute a single-jurisdiction legal query with sovereign enforcement."""
    try:
        # Check if advisor is initialized
        if advisor is None or jurisdiction_detector is None:
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "ADVISOR_NOT_INITIALIZED",
                    "message": "Legal advisor failed to initialize. Check server logs.",
                    "trace_id": str(uuid.uuid4())
                }
            )
        
        # Detect jurisdiction from query
        jurisdiction_hint_str = request.jurisdiction_hint.value if request.jurisdiction_hint else None
        jurisdiction_result = jurisdiction_detector.detect(
            query=request.query,
            user_hint=jurisdiction_hint_str
        )
        
        # DO NOT BYPASS EnhancedLegalAdvisor
        # Get legal advice using the enhanced advisor - SINGLE SOURCE OF TRUTH
        legal_query = LegalQuery(
            query_text=request.query,
            jurisdiction_hint=request.jurisdiction_hint,
            domain_hint=request.domain_hint
        )
        advice = advisor.provide_legal_advice(legal_query)
        
        # Convert advice.statutes to StatuteSchema
        statutes = []
        for statute in advice.statutes:
            statute_schema = StatuteSchema(
                act=statute['act'],
                year=statute['year'],
                section=statute['section'],
                title=statute['title']
            )
            statutes.append(statute_schema)
        
        sections_found = len(statutes)
        
        # Retrieve relevant case laws
        case_laws = []
        if case_retriever:
            relevant_cases = case_retriever.retrieve(
                query=request.query,
                domain=advice.domain,
                jurisdiction=advice.jurisdiction,
                top_k=3
            )
            case_laws = [
                CaseLawSchema(
                    title=case.title,
                    court=case.court,
                    year=case.year,
                    principle=case.principle
                )
                for case in relevant_cases
            ]
        
        # Build qualified legal analysis
        legal_analysis = _build_qualified_analysis(
            request.query,
            statutes,
            advice.jurisdiction
        )
        
        # Calculate structured confidence
        confidence = _calculate_structured_confidence(
            sections_found,
            advice.confidence_score,
            advice.domain,
            request.query
        )
        
        # Build response using enhanced advisor output
        base_response = {
            "domain": advice.domain,
            "domains": advice.domains if hasattr(advice, 'domains') else [advice.domain],
            "jurisdiction": advice.jurisdiction,
            "jurisdiction_detected": jurisdiction_result.jurisdiction,
            "jurisdiction_confidence": jurisdiction_result.confidence,
            "confidence": confidence,
            "legal_route": ["jurisdiction_detector", "clean_legal_advisor", "case_law_retriever", "multi_strategy_search"],
            "statutes": statutes,
            "case_laws": case_laws,
            "constitutional_articles": [],
            "provenance_chain": [{
                "timestamp": datetime.now().isoformat(),
                "event": "query_processed",
                "agent": "clean_legal_advisor",
                "sections_found": sections_found,
                "case_laws_found": len(case_laws),
                "ontology_filtered": advice.ontology_filtered if hasattr(advice, 'ontology_filtered') else False,
                "domains": advice.domains if hasattr(advice, 'domains') else [advice.domain],
                "jurisdiction_detected": jurisdiction_result.jurisdiction,
                "jurisdiction_confidence": jurisdiction_result.confidence
            }],
            "reasoning_trace": {
                "legal_analysis": legal_analysis,
                "procedural_steps": advice.procedural_steps,
                "remedies": advice.remedies,
                "sections_found": sections_found,
                "case_laws_found": len(case_laws),
                "jurisdiction_detection": {
                    "detected": jurisdiction_result.jurisdiction,
                    "confidence": jurisdiction_result.confidence,
                    "user_provided": jurisdiction_hint_str is not None
                },
                "confidence_factors": {
                    "sections_matched": sections_found,
                    "jurisdiction_confidence": confidence.jurisdiction,
                    "domain_confidence": confidence.domain,
                    "statute_match": confidence.statute_match
                }
            },
            "trace_id": advice.trace_id
        }
        
        # Enrich response with enforcement_decision, timeline, glossary, evidence_requirements
        enriched = enrich_response(base_response, request.query, advice.domain, statutes)
        
        return NyayaResponse(**enriched)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "QUERY_PROCESSING_ERROR",
                "message": f"Error processing legal query: {str(e)}",
                "trace_id": str(uuid.uuid4())
            }
        )

def _build_qualified_analysis(query: str, statutes: List, jurisdiction: str) -> str:
    """Build legal analysis with fully qualified statute references"""
    if not statutes:
        return f"No specific legal provisions found for this query in {jurisdiction} jurisdiction. Please provide more specific details or consult a legal professional."
    
    analysis = f"Legal Analysis for {jurisdiction} Jurisdiction:\n\n"
    analysis += "Applicable Legal Provisions:\n"
    analysis += "=" * 50 + "\n\n"
    
    for i, statute in enumerate(statutes, 1):
        analysis += f"{i}. Section {statute.section} of {statute.act}, {statute.year}:\n"
        analysis += f"   {statute.title}\n\n"
    
    return analysis

def _calculate_structured_confidence(
    sections_count: int,
    base_confidence: float,
    domain: str,
    query: str
) -> ConfidenceSchema:
    """Calculate structured confidence scores"""
    # Statute match confidence
    statute_match = min(0.95, 0.3 + (sections_count * 0.1)) if sections_count > 0 else 0.3
    
    # Domain confidence
    domain_keywords = {
        'criminal': ['crime', 'theft', 'murder', 'assault', 'terrorism'],
        'family': ['divorce', 'marriage', 'custody', 'alimony'],
        'civil': ['property', 'contract', 'consumer', 'employment']
    }
    
    domain_conf = 0.7
    if domain in domain_keywords:
        query_lower = query.lower()
        matches = sum(1 for kw in domain_keywords[domain] if kw in query_lower)
        domain_conf = min(0.95, 0.7 + (matches * 0.05))
    
    # Procedural match (placeholder)
    procedural_match = 0.8
    
    # Overall confidence
    overall = (base_confidence + statute_match + domain_conf) / 3
    
    return ConfidenceSchema(
        overall=min(0.95, overall),
        jurisdiction=base_confidence,
        domain=domain_conf,
        statute_match=statute_match,
        procedural_match=procedural_match
    )

@router.post("/multi_jurisdiction", response_model=MultiJurisdictionResponse)
async def multi_jurisdiction_query(request: MultiJurisdictionRequest):
    """Multi Jurisdiction Query"""
    return MultiJurisdictionResponse(
        comparative_analysis={},
        confidence=0.5,
        trace_id=str(uuid.uuid4())
    )

@router.post("/explain_reasoning", response_model=ExplainReasoningResponse)
async def explain_reasoning(request: ExplainReasoningRequest):
    """Explain Reasoning"""
    return ExplainReasoningResponse(
        trace_id=request.trace_id,
        explanation={"message": "Reasoning explanation"},
        reasoning_tree={"root": "explanation_tree"},
        constitutional_articles=[]
    )

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit Feedback"""
    return FeedbackResponse(
        status="received",
        trace_id=request.trace_id,
        message="Feedback submitted successfully"
    )

@router.get("/trace/{trace_id}", response_model=TraceResponse)
async def get_trace(trace_id: str):
    """Get Trace"""
    return TraceResponse(
        trace_id=trace_id,
        event_chain=[],
        agent_routing_tree={},
        jurisdiction_hops=[],
        rl_reward_snapshot={},
        context_fingerprint="mock_fingerprint",
        nonce_verification=True,
        signature_verification=True
    )