from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List
import asyncio
from api.schemas import (
    QueryRequest, MultiJurisdictionRequest, ExplainReasoningRequest,
    FeedbackRequest, NyayaResponse, MultiJurisdictionResponse,
    ExplainReasoningResponse, FeedbackResponse, TraceResponse
)
from api.dependencies import get_trace_id, validate_nonce, emit_query_received_event
from api.response_builder import ResponseBuilder
from sovereign_agents.jurisdiction_router_agent import JurisdictionRouterAgent
from sovereign_agents.legal_agent import LegalAgent
from sovereign_agents.constitutional_agent import ConstitutionalAgent
from jurisdiction_router.router import JurisdictionRouter
from rl_engine.feedback_api import FeedbackAPI
from provenance_chain.lineage_tracer import tracer
from provenance_chain.hash_chain_ledger import ledger
from provenance_chain.event_signer import signer
from enforcement_engine.engine import (
    EnforcementSignal,
    get_enforcement_response,
    is_execution_permitted
)
from enforcement_provenance.ledger import (
    log_enforcement_decision,
    log_routing_decision,
    log_agent_execution,
    log_rl_update,
    log_refusal_or_escalation
)
from governed_execution.pipeline import execute_governed_agent

router = APIRouter(prefix="/nyaya", tags=["nyaya"])

# Initialize agents and components
jurisdiction_router_agent = JurisdictionRouterAgent()
jurisdiction_router = JurisdictionRouter()
feedback_api = FeedbackAPI()

# Agent instances for different jurisdictions
agents = {
    "IN": LegalAgent(agent_id="india_legal_agent", jurisdiction="India"),
    "UK": LegalAgent(agent_id="uk_legal_agent", jurisdiction="UK"),
    "UAE": LegalAgent(agent_id="uae_legal_agent", jurisdiction="UAE")
}

@router.post("/query", response_model=NyayaResponse)
async def query_legal(
    request: QueryRequest,
    trace_id: str = Depends(get_trace_id),
    nonce: str = Depends(validate_nonce),
    background_tasks: BackgroundTasks = None
):
    """Execute a single-jurisdiction legal query with sovereign enforcement."""
    try:
        # Emit query received event
        background_tasks.add_task(
            emit_query_received_event,
            request.query,
            trace_id
        )

        # Step 1: Call JurisdictionRouterAgent
        routing_result = await jurisdiction_router_agent.process({
            "query": request.query,
            "jurisdiction_hint": request.jurisdiction_hint,
            "domain_hint": request.domain_hint
        })

        target_jurisdiction = routing_result["target_jurisdiction"]
        target_agent_id = routing_result["target_agent"]
        
        # Log routing decision to provenance
        routing_details = {
            "query": request.query,
            "jurisdiction_hint": request.jurisdiction_hint,
            "domain_hint": request.domain_hint,
            "target_jurisdiction": target_jurisdiction,
            "target_agent": target_agent_id
        }
        log_routing_decision(trace_id, routing_details)

        # Create enforcement signal based on routing result
        enforcement_signal = EnforcementSignal(
            case_id=trace_id,
            country=target_jurisdiction,
            domain=request.domain_hint or "general",
            procedure_id="query_procedure",
            original_confidence=routing_result.get("confidence", 0.5),
            user_request=request.query,
            jurisdiction_routed_to=target_jurisdiction,
            trace_id=trace_id
        )
        
        # Check if execution is permitted by enforcement engine
        if not is_execution_permitted(enforcement_signal):
            # Log refusal to provenance
            refusal_details = {
                "reason": "enforcement_blocked",
                "query": request.query,
                "target_jurisdiction": target_jurisdiction
            }
            log_refusal_or_escalation(trace_id, refusal_details)
            
            # Return governed response with enforcement proof
            return get_enforcement_response(enforcement_signal)

        # Step 2: Route to appropriate LegalAgent
        if target_jurisdiction not in agents:
            raise HTTPException(
                status_code=400,
                detail=ResponseBuilder.build_error_response(
                    "JURISDICTION_NOT_SUPPORTED",
                    f"Jurisdiction {target_jurisdiction} not supported",
                    trace_id
                ).dict()
            )

        # Execute agent through governed pipeline
        agent = agents[target_jurisdiction]
        def execute_agent(context):
            return agent.process({
                "query": context["query"],
                "trace_id": context["trace_id"]
            })
            
        agent_context = {
            "query": request.query,
            "trace_id": trace_id,
            "case_id": trace_id,
            "country": target_jurisdiction,
            "domain": request.domain_hint or "general",
            "procedure_id": "legal_agent_processing",
            "original_confidence": routing_result.get("confidence", 0.5),
            "user_request": request.query,
            "jurisdiction_routed_to": target_jurisdiction
        }
        
        agent_result = execute_governed_agent(execute_agent, agent_context, trace_id)
        
        # Log agent execution to provenance
        execution_details = {
            "agent_id": agent.agent_id,
            "jurisdiction": target_jurisdiction,
            "query_processed": request.query[:100] + "..." if len(request.query) > 100 else request.query
        }
        log_agent_execution(trace_id, execution_details)

        # Extract confidence from result (could be from governed result or direct agent result)
        if isinstance(agent_result, dict) and "result" in agent_result:
            # Result came from governed execution
            actual_result = agent_result["result"]
            confidence = actual_result.get("confidence", 0.5)
        else:
            # Direct agent result
            actual_result = agent_result
            confidence = agent_result.get("confidence", 0.5)
            
        domain = request.domain_hint or "general"
        legal_route = [jurisdiction_router_agent.agent_id, agent.agent_id]

        # Placeholder for provenance chain and reasoning trace
        provenance_chain = []
        reasoning_trace = {
            "routing_decision": routing_result,
            "agent_processing": actual_result
        }

        # Emit decision explained event
        background_tasks.add_task(
            _emit_decision_explained_event,
            trace_id,
            confidence,
            legal_route
        )

        # Build final response
        response = ResponseBuilder.build_nyaya_response(
            domain=domain,
            jurisdiction=target_jurisdiction,
            confidence=confidence,
            legal_route=legal_route,
            trace_id=trace_id,
            provenance_chain=provenance_chain,
            reasoning_trace=reasoning_trace
        )
        
        # If agent result had enforcement metadata, merge it
        if isinstance(agent_result, dict):
            if "enforcement_metadata" in agent_result:
                response.enforcement_metadata = agent_result["enforcement_metadata"]
            if "trace_proof" in agent_result:
                response.provenance_chain = [agent_result["trace_proof"]]

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ResponseBuilder.build_error_response(
                "INTERNAL_ERROR",
                "An internal error occurred",
                trace_id
            ).dict()
        )

@router.post("/multi_jurisdiction", response_model=MultiJurisdictionResponse)
async def multi_jurisdiction_query(
    request: MultiJurisdictionRequest,
    trace_id: str = Depends(get_trace_id),
    nonce: str = Depends(validate_nonce),
    background_tasks: BackgroundTasks = None
):
    """Execute parallel legal analysis across multiple jurisdictions with sovereign enforcement."""
    try:
        # Emit query received event
        background_tasks.add_task(
            emit_query_received_event,
            request.query,
            trace_id
        )

        comparative_analysis = {}
        confidences = []

        # Execute agents in parallel with enforcement checks
        for jurisdiction in request.jurisdictions:
            jur_value = jurisdiction.value
            if jur_value not in agents:
                continue
            
            # Create enforcement signal for this jurisdiction
            enforcement_signal = EnforcementSignal(
                case_id=f"{trace_id}_{jur_value}",
                country=jur_value,
                domain="multi",
                procedure_id="multi_jurisdiction_query",
                original_confidence=0.5,
                user_request=request.query,
                jurisdiction_routed_to=jur_value,
                trace_id=f"{trace_id}_{jur_value}"
            )
            
            # Check if execution is permitted by enforcement engine
            if not is_execution_permitted(enforcement_signal):
                # Log refusal to provenance
                refusal_details = {
                    "reason": "enforcement_blocked",
                    "query": request.query,
                    "target_jurisdiction": jur_value
                }
                log_refusal_or_escalation(f"{trace_id}_{jur_value}", refusal_details)
                
                # Skip this jurisdiction if enforcement blocks it
                continue

            agent = agents[jur_value]
            
            # Execute agent through governed pipeline
            def execute_agent(context):
                return agent.process({
                    "query": context["query"],
                    "trace_id": context["trace_id"]
                })
                
            agent_context = {
                "query": request.query,
                "trace_id": f"{trace_id}_{jur_value}",
                "case_id": f"{trace_id}_{jur_value}",
                "country": jur_value,
                "domain": "multi",
                "procedure_id": "legal_agent_processing",
                "original_confidence": 0.5,
                "user_request": request.query,
                "jurisdiction_routed_to": jur_value
            }
            
            agent_result = execute_governed_agent(execute_agent, agent_context, f"{trace_id}_{jur_value}")
            
            # Log agent execution to provenance
            execution_details = {
                "agent_id": agent.agent_id,
                "jurisdiction": jur_value,
                "query_processed": request.query[:100] + "..." if len(request.query) > 100 else request.query
            }
            log_agent_execution(f"{trace_id}_{jur_value}", execution_details)

            # Extract result and confidence
            if isinstance(agent_result, dict) and "result" in agent_result:
                # Result came from governed execution
                actual_result = agent_result["result"]
                confidence = actual_result.get("confidence", 0.5)
            else:
                # Direct agent result
                actual_result = agent_result
                confidence = agent_result.get("confidence", 0.5)

            confidences.append(confidence)

            comparative_analysis[jurisdiction] = ResponseBuilder.build_nyaya_response(
                domain="multi",
                jurisdiction=jurisdiction,
                confidence=confidence,
                legal_route=[agents[jur_value].agent_id],
                trace_id=f"{trace_id}_{jurisdiction.lower()}",
                provenance_chain=[],
                reasoning_trace=actual_result
            )

        # Calculate aggregate confidence (mean)
        aggregate_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return ResponseBuilder.build_multi_jurisdiction_response(
            comparative_analysis=comparative_analysis,
            confidence=aggregate_confidence,
            trace_id=trace_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ResponseBuilder.build_error_response(
                "INTERNAL_ERROR",
                "An internal error occurred",
                trace_id
            ).dict()
        )

@router.post("/explain_reasoning", response_model=ExplainReasoningResponse)
async def explain_reasoning(
    request: ExplainReasoningRequest,
    trace_id: str = Depends(get_trace_id),
    nonce: str = Depends(validate_nonce)
):
    """Explain reasoning without re-executing agents."""
    try:
        return ResponseBuilder.build_explain_reasoning_response(
            request.trace_id,
            request.explanation_level.value
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=ResponseBuilder.build_error_response(
                "TRACE_NOT_FOUND",
                f"Trace {request.trace_id} not found",
                trace_id
            ).dict()
        )

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    trace_id: str = Depends(get_trace_id),
    nonce: str = Depends(validate_nonce),
    background_tasks: BackgroundTasks = None
):
    """Submit system-level RL feedback with sovereign enforcement."""
    try:
        # Create enforcement signal for feedback
        enforcement_signal = EnforcementSignal(
            case_id=request.trace_id,
            country="global",
            domain="feedback",
            procedure_id="feedback_submission",
            original_confidence=0.5,
            user_request=f"Rating: {request.rating}, Type: {request.feedback_type}",
            jurisdiction_routed_to="global",
            trace_id=request.trace_id,
            user_feedback="positive" if request.rating >= 4 else "negative" if request.rating <= 2 else "neutral",
            outcome_tag="feedback_submitted"
        )
        
        # Check if RL update is permitted by enforcement engine
        rl_permitted = is_execution_permitted(enforcement_signal)
        
        if rl_permitted:
            # Forward to RL engine
            feedback_result = feedback_api.receive_feedback({
                "trace_id": request.trace_id,
                "score": request.rating,
                "nonce": nonce,
                "comment": request.comment
            })
            
            # Log RL update to provenance
            rl_details = {
                "trace_id": request.trace_id,
                "rating": request.rating,
                "feedback_type": request.feedback_type.value,
                "comment": request.comment
            }
            log_rl_update(request.trace_id, rl_details)
        else:
            # Log refusal to provenance
            refusal_details = {
                "reason": "enforcement_blocked_rl",
                "trace_id": request.trace_id,
                "rating": request.rating
            }
            log_refusal_or_escalation(request.trace_id, refusal_details)
            
            # Return governed response with enforcement proof
            return get_enforcement_response(enforcement_signal)

        # Emit feedback received event
        background_tasks.add_task(
            _emit_feedback_received_event,
            request.trace_id,
            request.rating,
            request.feedback_type.value
        )

        return ResponseBuilder.build_feedback_response(
            status="recorded",
            trace_id=request.trace_id,
            message="Feedback recorded successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ResponseBuilder.build_error_response(
                "FEEDBACK_ERROR",
                "Failed to process feedback",
                trace_id
            ).dict()
        )

@router.get("/trace/{trace_id}", response_model=TraceResponse)
async def get_trace(trace_id: str):
    """Get full sovereign audit trail."""
    try:
        return ResponseBuilder.build_trace_response(trace_id)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=ResponseBuilder.build_error_response(
                "TRACE_NOT_FOUND",
                f"Trace {trace_id} not found",
                trace_id
            ).dict()
        )

# Helper functions for background tasks
async def _emit_decision_explained_event(trace_id: str, confidence: float, legal_route: List[str]):
    """Emit decision explained event."""
    event = {
        "timestamp": "current_timestamp",
        "agent_id": "api_gateway",
        "jurisdiction": "global",
        "event_name": "decision_explained",
        "request_hash": hash(str(legal_route)) % (10 ** 8),
        "details": {
            "confidence": confidence,
            "legal_route": legal_route
        }
    }
    # In real implementation, this would be added to the ledger

async def _emit_feedback_received_event(trace_id: str, rating: int, feedback_type: str):
    """Emit feedback received event."""
    event = {
        "timestamp": "current_timestamp",
        "agent_id": "api_gateway",
        "jurisdiction": "global",
        "event_name": "feedback_received",
        "request_hash": hash(f"{trace_id}:{rating}") % (10 ** 8),
        "details": {
            "rating": rating,
            "feedback_type": feedback_type
        }
    }
    # In real implementation, this would be added to the ledger