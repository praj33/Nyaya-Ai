"""Integration module for connecting procedure intelligence with legal agents."""
from typing import Dict, Any, Optional
from procedures.intelligence import procedure_intelligence


class ProcedureAgentIntegration:
    """Integrates procedure intelligence with legal agents."""
    
    def __init__(self):
        self.intelligence = procedure_intelligence
    
    def enrich_legal_response(
        self,
        agent_response: Dict[str, Any],
        country: str,
        domain: str,
        query: str
    ) -> Dict[str, Any]:
        """Enrich legal agent response with procedure intelligence."""
        enriched = agent_response.copy()
        
        # Add procedure summary
        procedure_summary = self.intelligence.get_procedure_summary(country, domain)
        if "error" not in procedure_summary:
            enriched["procedure_context"] = {
                "total_steps": procedure_summary.get("total_steps"),
                "timelines": procedure_summary.get("timelines"),
                "authorities": procedure_summary.get("authorities"),
                "key_steps": procedure_summary.get("key_steps", [])[:5]  # First 5 steps
            }
        
        return enriched
    
    def suggest_next_actions(
        self,
        country: str,
        domain: str,
        current_step: str,
        outcome: Optional[str] = None
    ) -> Dict[str, Any]:
        """Suggest next actions based on current procedural step."""
        next_steps = self.intelligence.get_next_steps(country, domain, current_step, outcome)
        
        return {
            "current_step": current_step,
            "outcome": outcome,
            "suggested_next_steps": next_steps,
            "total_options": len(next_steps)
        }
    
    def assess_case_readiness(
        self,
        country: str,
        domain: str,
        canonical_step: str,
        available_documents: list
    ) -> Dict[str, Any]:
        """Assess case readiness for a specific procedural step."""
        assessment = self.intelligence.assess_evidence_readiness(
            canonical_step=canonical_step,
            available_documents=available_documents
        )
        
        # Add recommendations
        if assessment["evidence_state"] != "EVIDENCE_COMPLETE":
            assessment["recommendations"] = [
                f"Obtain {doc}" for doc in assessment["missing_documents"]
            ]
        else:
            assessment["recommendations"] = ["All mandatory documents are available. Proceed with confidence."]
        
        return assessment
    
    def get_jurisdiction_mapping(self, jurisdiction: str) -> str:
        """Map jurisdiction codes to country names used in procedures."""
        mapping = {
            "IN": "india",
            "India": "india",
            "UK": "uk",
            "United Kingdom": "uk",
            "UAE": "uae",
            "United Arab Emirates": "uae",
            "KSA": "ksa",
            "Saudi Arabia": "ksa"
        }
        return mapping.get(jurisdiction, jurisdiction.lower())
    
    def get_domain_mapping(self, domain_hint: Optional[str]) -> str:
        """Map domain hints to procedure domain names."""
        if not domain_hint:
            return "criminal"
        
        mapping = {
            "criminal": "criminal",
            "civil": "civil",
            "constitutional": "civil",  # Map to civil for now
            "family": "family",
            "consumer": "consumer_commercial",
            "commercial": "consumer_commercial"
        }
        return mapping.get(domain_hint.lower(), "criminal")


# Global instance
procedure_agent_integration = ProcedureAgentIntegration()
