"""Enhanced Legal Agent with comprehensive database integration."""
from sovereign_agents.base_agent import BaseAgent
from legal_database.database_loader import legal_db
from legal_database.enhanced_response_builder import enhanced_response_builder
from typing import Dict, Any, List
import asyncio

class EnhancedLegalAgent(BaseAgent):
    """Enhanced Legal Agent with comprehensive legal database integration."""
    
    def __init__(self, agent_id: str = None, jurisdiction: str = None, capabilities: List[str] = None):
        super().__init__(agent_id, jurisdiction, capabilities or ["legal_analysis", "database_lookup", "procedure_guidance"])
        
    async def process(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Process legal queries with comprehensive database integration."""
        await asyncio.sleep(0.1)
        
        query_text = query.get("query", "")
        jurisdiction = self.jurisdiction or query.get("jurisdiction", "IN")
        domain_classification = query.get("domain_classification", {})
        
        # Get enhanced legal response
        enhanced_response = enhanced_response_builder.build_enhanced_legal_response(
            query=query_text,
            jurisdiction=jurisdiction,
            domain_hint=domain_classification.get("domain"),
            confidence=self.generate_confidence_score(query),
            trace_id=query.get("trace_id", "")
        )
        
        # Build agent result with enhanced data
        result = {
            "query_type": "enhanced_legal",
            "jurisdiction": jurisdiction,
            "action": "comprehensive_analysis",
            "confidence": enhanced_response["confidence"],
            "domain_analysis": enhanced_response["domain_classification"],
            "legal_provisions": enhanced_response["legal_provisions"],
            "procedural_guidance": enhanced_response["procedural_guidance"],
            "risk_assessment": enhanced_response["risk_assessment"],
            "cross_jurisdictional_notes": enhanced_response["cross_jurisdictional_notes"],
            "enhanced_analysis": True
        }
        
        # Emit enhanced event
        self.emit_event("enhanced_legal_analysis", {
            "classification": "comprehensive_legal_query",
            "provisions_found": len(enhanced_response["legal_provisions"]["relevant_sections"]),
            "domain": enhanced_response["domain"],
            "risk_level": enhanced_response["risk_assessment"]["risk_level"]
        })
        
        return result