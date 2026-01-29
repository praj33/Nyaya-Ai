from typing import Dict, Any, List
from api.schemas import (
    NyayaResponse, MultiJurisdictionResponse, ExplainReasoningResponse,
    FeedbackResponse, TraceResponse, ErrorResponse
)
from provenance_chain.lineage_tracer import tracer
from provenance_chain.hash_chain_ledger import ledger
from provenance_chain.event_signer import signer

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
        constitutional_articles: List[str] = None
    ) -> NyayaResponse:
        """Build a standardized Nyaya response."""
        return NyayaResponse(
            domain=domain,
            jurisdiction=jurisdiction,
            confidence=confidence,
            legal_route=legal_route,
            constitutional_articles=constitutional_articles or [],
            provenance_chain=provenance_chain or [],
            reasoning_trace=reasoning_trace or {},
            trace_id=trace_id
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
        message: str
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
        # Get event chain from ledger
        event_chain = ledger.get_all_entries()

        # Filter events for this trace_id
        trace_events = [
            event for event in event_chain
            if event.get("signed_event", {}).get("trace_id") == trace_id
        ]

        # Build agent routing tree
        agent_routing_tree = ResponseBuilder._build_agent_routing_tree(trace_events)

        # Get jurisdiction hops
        jurisdiction_hops = ResponseBuilder._extract_jurisdiction_hops(trace_events)

        # Placeholder for RL reward snapshot
        rl_reward_snapshot = {"placeholder": "RL data would be fetched here"}

        # Generate context fingerprint (placeholder)
        context_fingerprint = "placeholder_fingerprint"

        # Check nonce and signature verification
        nonce_verification = ResponseBuilder._verify_nonces(trace_events)
        signature_verification = ResponseBuilder._verify_signatures(trace_events)

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
    def _build_agent_routing_tree(events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build hierarchical tree of agent routing decisions."""
        tree = {"root": "api_gateway", "children": {}}

        for event in events:
            agent_id = event.get("agent_id", "unknown")
            if agent_id not in tree["children"]:
                tree["children"][agent_id] = {
                    "jurisdiction": event.get("jurisdiction"),
                    "events": []
                }
            tree["children"][agent_id]["events"].append(event.get("event_name"))

        return tree

    @staticmethod
    def _extract_jurisdiction_hops(events: List[Dict[str, Any]]) -> List[str]:
        """Extract sequence of jurisdiction transitions."""
        hops = []
        for event in events:
            jurisdiction = event.get("jurisdiction")
            if jurisdiction and jurisdiction not in hops:
                hops.append(jurisdiction)
        return hops

    @staticmethod
    def _verify_nonces(events: List[Dict[str, Any]]) -> bool:
        """Verify nonce integrity across events."""
        # Placeholder - would check nonce chain validity
        return True

    @staticmethod
    def _verify_signatures(events: List[Dict[str, Any]]) -> bool:
        """Verify signature integrity across events."""
        # Placeholder - would verify HMAC signatures
        return True