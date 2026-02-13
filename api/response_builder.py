from typing import Dict, Any, List
from api.schemas import (
    NyayaResponse, MultiJurisdictionResponse, ExplainReasoningResponse,
    FeedbackResponse, TraceResponse, ErrorResponse
)
from provenance_chain.lineage_tracer import tracer
from provenance_chain.hash_chain_ledger import ledger
from provenance_chain.event_signer import signer
from enforcement_provenance.ledger import get_trace_history as get_enforcement_trace_history
from core.response.enricher import enrich_response

class ResponseBuilder:
    """Builds standardized responses for the Nyaya API Gateway."""

    @staticmethod   
    def build_nyaya_response(
        domain: str,
        jurisdiction: str,
        confidence: float,
        legal_route: List[str],
        trace_id: str,
        provenance_chain: List[Dict[str, Any]] = None,
        reasoning_trace: Dict[str, Any] = None,
        constitutional_articles: List[str] = None,
        query_text: str = "",
        statutes: List[Dict] = None
    ) -> NyayaResponse:
        """Build a standardized Nyaya response."""
        base_response = {
            "domain": domain,
            "jurisdiction": jurisdiction,
            "confidence": confidence,
            "legal_route": legal_route,
            "constitutional_articles": constitutional_articles or [],
            "provenance_chain": provenance_chain or [],
            "reasoning_trace": reasoning_trace or {},
            "trace_id": trace_id
        }
        
        # Enrich response with required fields
        enriched = enrich_response(base_response, query_text, domain, statutes or [])
        
        return NyayaResponse(
            domain=enriched["domain"],
            jurisdiction=enriched["jurisdiction"],
            confidence=enriched["confidence"],
            legal_route=enriched["legal_route"],
            constitutional_articles=enriched["constitutional_articles"],
            provenance_chain=enriched["provenance_chain"],
            reasoning_trace=enriched["reasoning_trace"],
            trace_id=enriched["trace_id"],
            enforcement_decision=enriched.get("enforcement_decision", "ALLOW"),
            timeline=enriched.get("timeline", []),
            glossary=enriched.get("glossary", []),
            evidence_requirements=enriched.get("evidence_requirements", [])
        )

    @staticmethod
    def build_multi_jurisdiction_response(
        comparative_analysis: Dict[str, NyayaResponse],
        confidence: float,
        trace_id: str
    ) -> MultiJurisdictionResponse:
        """Build a multi-jurisdiction response."""
        return MultiJurisdictionResponse(
            comparative_analysis=comparative_analysis,
            confidence=confidence,
            trace_id=trace_id
        )

    @staticmethod
    def build_explain_reasoning_response(
        trace_id: str,
        explanation_level: str
    ) -> ExplainReasoningResponse:
        """Build an explain reasoning response."""
        # Fetch trace data from provenance store
        trace_history = tracer.get_trace_history(trace_id)
        reasoning_tree = ResponseBuilder._construct_reasoning_tree(trace_history, explanation_level)

        # Extract constitutional articles if jurisdiction is India
        constitutional_articles = []
        if any(event.get("jurisdiction") == "India" for event in trace_history.get("events", [])):
            constitutional_articles = ResponseBuilder._extract_constitutional_articles(trace_history)

        return ExplainReasoningResponse(
            trace_id=trace_id,
            explanation={"level": explanation_level, "trace_data": trace_history},
            reasoning_tree=reasoning_tree,
            constitutional_articles=constitutional_articles
        )

    @staticmethod
    def build_feedback_response(
        status: str,
        trace_id: str,
        message: str,
        enforcement_data: Dict[str, Any] = None
    ) -> FeedbackResponse:
        """Build a feedback response."""
        return FeedbackResponse(
            status=status,
            trace_id=trace_id,
            message=message
        )

    @staticmethod
    def build_trace_response(trace_id: str) -> TraceResponse:
        """Build a full trace audit response."""
        # Get event chain from enforcement ledger (this contains the actual trace data)
        trace_events = get_enforcement_trace_history(trace_id)
            
        if not trace_events:
            raise ValueError(f"No trace events found for trace_id: {trace_id}")
            
        # Build agent routing tree
        agent_routing_tree = ResponseBuilder._build_agent_routing_tree_from_enforcement(trace_events)
            
        # Get jurisdiction hops
        jurisdiction_hops = ResponseBuilder._extract_jurisdiction_hops_from_enforcement(trace_events)
            
        # Placeholder for RL reward snapshot
        rl_reward_snapshot = {"placeholder": "RL data would be fetched here"}
            
        # Generate context fingerprint (placeholder)
        context_fingerprint = "placeholder_fingerprint"
            
        # Check nonce and signature verification
        nonce_verification = ResponseBuilder._verify_nonces_enforcement(trace_events)
        signature_verification = ResponseBuilder._verify_signatures_enforcement(trace_events)
            
        return TraceResponse(
            trace_id=trace_id,
            event_chain=trace_events,
            agent_routing_tree=agent_routing_tree,
            jurisdiction_hops=jurisdiction_hops,
            rl_reward_snapshot=rl_reward_snapshot,
            context_fingerprint=context_fingerprint,
            nonce_verification=nonce_verification,
            signature_verification=signature_verification
        )

    @staticmethod
    def build_error_response(
        error_code: str,
        message: str,
        trace_id: str
    ) -> ErrorResponse:
        """Build a standardized error response."""
        return ErrorResponse(
            error_code=error_code,
            message=message,
            trace_id=trace_id
        )

    @staticmethod
    def _construct_reasoning_tree(trace_history: Dict[str, Any], level: str) -> Dict[str, Any]:
        """Construct reasoning tree based on explanation level."""
        events = trace_history.get("events", [])

        if level == "brief":
            return {
                "summary": f"Query processed through {len(events)} steps",
                "key_decisions": [event.get("event_name") for event in events if event.get("event_name") in ["jurisdiction_resolved", "agent_classified"]]
            }
        elif level == "detailed":
            return {
                "full_timeline": events,
                "agent_interactions": [
                    {
                        "agent": event.get("agent_id"),
                        "action": event.get("event_name"),
                        "details": event.get("details", {})
                    } for event in events
                ]
            }
        elif level == "constitutional":
            return {
                "constitutional_focus": [
                    event for event in events
                    if event.get("jurisdiction") == "India" or "constitutional" in str(event.get("details", {}))
                ],
                "articles_referenced": ResponseBuilder._extract_constitutional_articles(trace_history)
            }
        else:
            return {"error": "Invalid explanation level"}

    @staticmethod
    def _extract_constitutional_articles(trace_history: Dict[str, Any]) -> List[str]:
        """Extract constitutional articles from trace history."""
        # Placeholder implementation - in real system would parse agent responses
        return ["Article 14", "Article 19", "Article 21"]  # Example articles

    @staticmethod
    def _build_agent_routing_tree_from_enforcement(events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build hierarchical tree of agent routing decisions from enforcement ledger."""
        tree = {"root": "api_gateway", "children": {}}
            
        for event in events:
            event_type = event.get("type", "unknown")
            trace_id = event.get("trace_id", "unknown")
                
            if event_type == "routing_decision":
                details = event.get("routing_details", {})
                target_jurisdiction = details.get("target_jurisdiction", "unknown")
                target_agent = details.get("target_agent", "unknown")
                    
                if target_agent not in tree["children"]:
                    tree["children"][target_agent] = {
                        "jurisdiction": target_jurisdiction,
                        "events": []
                    }
                tree["children"][target_agent]["events"].append("routing_decision")
                    
            elif event_type == "agent_execution":
                details = event.get("execution_details", {})
                agent_id = details.get("agent_id", "unknown")
                jurisdiction = details.get("jurisdiction", "unknown")
                    
                if agent_id not in tree["children"]:
                    tree["children"][agent_id] = {
                        "jurisdiction": jurisdiction,
                        "events": []
                    }
                tree["children"][agent_id]["events"].append("agent_execution")
                    
            elif event_type == "refusal_or_escalation":
                if "refusal_handler" not in tree["children"]:
                    tree["children"]["refusal_handler"] = {
                        "jurisdiction": "global",
                        "events": []
                    }
                tree["children"]["refusal_handler"]["events"].append("refusal_or_escalation")
            
        return tree
    
    @staticmethod
    def _extract_jurisdiction_hops_from_enforcement(events: List[Dict[str, Any]]) -> List[str]:
        """Extract sequence of jurisdiction transitions from enforcement ledger."""
        hops = []
        for event in events:
            event_type = event.get("type")
                
            if event_type == "routing_decision":
                details = event.get("routing_details", {})
                jurisdiction = details.get("target_jurisdiction")
                if jurisdiction and jurisdiction not in hops:
                    hops.append(jurisdiction)
            elif event_type == "agent_execution":
                details = event.get("execution_details", {})
                jurisdiction = details.get("jurisdiction")
                if jurisdiction and jurisdiction not in hops:
                    hops.append(jurisdiction)
                        
        return hops
    
    @staticmethod
    def _verify_nonces_enforcement(events: List[Dict[str, Any]]) -> bool:
        """Verify nonce integrity across enforcement events."""
        # Placeholder - would check nonce chain validity in enforcement ledger
        return True
    
    @staticmethod
    def _verify_signatures_enforcement(events: List[Dict[str, Any]]) -> bool:
        """Verify signature integrity across enforcement events."""
        # Placeholder - would verify HMAC signatures in enforcement ledger
        return True