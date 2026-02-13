"""Enhanced response builder with legal database integration."""
from typing import Dict, Any, List, Optional
from legal_database.database_loader import legal_db
from procedures.integration import procedure_agent_integration
from procedures.loader import procedure_loader

class EnhancedResponseBuilder:
    """Enhanced response builder with comprehensive legal database integration."""
    
    @staticmethod
    def build_enhanced_legal_response(
        query: str,
        jurisdiction: str,
        domain_hint: Optional[str] = None,
        confidence: float = 0.5,
        trace_id: str = ""
    ) -> Dict[str, Any]:
        """Build enhanced legal response with database integration."""
        
        # Classify query domain
        domain_classification = legal_db.classify_query_domain(query, jurisdiction)
        final_domain = domain_hint or domain_classification["domain"]
        
        # Get relevant legal sections
        legal_sections = legal_db.get_legal_sections(query, jurisdiction, final_domain)
        
        # Get procedure guidance
        country_code = procedure_agent_integration.get_jurisdiction_mapping(jurisdiction)
        domain_code = procedure_agent_integration.get_domain_mapping(final_domain)
        
        try:
            procedure_summary = procedure_agent_integration.intelligence.get_procedure_summary(country_code, domain_code)
        except:
            procedure_summary = {"error": "Procedure data not available"}
        
        # Build enhanced response
        response = {
            "query": query,
            "jurisdiction": jurisdiction,
            "domain": final_domain,
            "confidence": confidence,
            "trace_id": trace_id,
            "domain_classification": {
                "classified_domain": domain_classification["domain"],
                "classification_confidence": domain_classification["confidence"],
                "matched_subdomains": domain_classification["subdomains"],
                "confidence_threshold": domain_classification["threshold"]
            },
            "legal_provisions": {
                "relevant_sections": legal_sections,
                "total_matches": len(legal_sections)
            },
            "procedural_guidance": {
                "procedure_summary": procedure_summary if "error" not in procedure_summary else None,
                "next_steps": EnhancedResponseBuilder._get_next_steps(jurisdiction, final_domain),
                "required_documents": EnhancedResponseBuilder._get_required_documents(jurisdiction, final_domain),
                "estimated_timeline": EnhancedResponseBuilder._get_timeline(jurisdiction, final_domain)
            },
            "cross_jurisdictional_notes": EnhancedResponseBuilder._get_cross_jurisdictional_notes(final_domain),
            "risk_assessment": EnhancedResponseBuilder._assess_risks(legal_sections, final_domain)
        }
        
        return response
    
    @staticmethod
    def _get_next_steps(jurisdiction: str, domain: str) -> List[str]:
        """Get next steps based on jurisdiction and domain."""
        procedure = procedure_loader.get_procedure(jurisdiction.lower(), domain.lower())
        if procedure and "procedure" in procedure and "steps" in procedure["procedure"]:
            steps = procedure["procedure"]["steps"]
            return [f"{step.get('title', '')}" for step in steps[:5]]
        return ["Consult legal counsel", "Gather evidence", "File appropriate action"]
    
    @staticmethod
    def _get_required_documents(jurisdiction: str, domain: str) -> List[str]:
        """Get required documents based on jurisdiction and domain."""
        procedure = procedure_loader.get_procedure(jurisdiction.lower(), domain.lower())
        if procedure and "procedure" in procedure and "documents_required" in procedure["procedure"]:
            return procedure["procedure"]["documents_required"]
        return ["Legal documents", "Evidence", "Witness statements"]
    
    @staticmethod
    def _get_timeline(jurisdiction: str, domain: str) -> str:
        """Get estimated timeline based on jurisdiction and domain."""
        procedure = procedure_loader.get_procedure(jurisdiction.lower(), domain.lower())
        if procedure and "procedure" in procedure and "timelines" in procedure["procedure"]:
            timelines = procedure["procedure"]["timelines"]
            return f"Best: {timelines.get('best_case', 'N/A')}, Average: {timelines.get('average', 'N/A')}, Worst: {timelines.get('worst_case', 'N/A')}"
        return "12-24 months average"
    
    @staticmethod
    def _get_cross_jurisdictional_notes(domain: str) -> List[str]:
        """Get cross-jurisdictional comparison notes."""
        notes_map = {
            "criminal": [
                "Criminal procedures vary significantly across jurisdictions",
                "Evidence requirements may differ",
                "Punishment scales vary by jurisdiction",
                "Appeal processes differ"
            ],
            "civil": [
                "Civil procedures have common law similarities",
                "Contract law principles are generally consistent",
                "Enforcement mechanisms vary",
                "Alternative dispute resolution availability differs"
            ],
            "family": [
                "Personal status laws vary significantly",
                "Religious law applications differ",
                "Child custody standards vary",
                "International enforcement challenges exist"
            ]
        }
        
        return notes_map.get(domain, ["Legal systems vary across jurisdictions", "Local legal counsel recommended"])
    
    @staticmethod
    def _assess_risks(legal_sections: List[Dict[str, Any]], domain: str) -> Dict[str, Any]:
        """Assess risks based on legal sections and domain."""
        risk_level = "Medium"
        risk_factors = []
        
        if legal_sections:
            # Check for serious offenses
            serious_keywords = ["murder", "rape", "terrorism", "life imprisonment", "death penalty"]
            if any(any(keyword in str(section).lower() for keyword in serious_keywords) for section in legal_sections):
                risk_level = "High"
                risk_factors.append("Serious criminal charges involved")
            
            # Check for complex procedures
            if len(legal_sections) > 3:
                risk_factors.append("Multiple legal provisions applicable")
            
            # Domain-specific risks
            if domain == "criminal":
                risk_factors.extend(["Criminal record implications", "Potential imprisonment", "Legal costs"])
            elif domain == "civil":
                risk_factors.extend(["Financial liability", "Time-consuming process", "Legal costs"])
        
        if not risk_factors:
            risk_factors = ["Standard legal proceedings", "Moderate complexity"]
            risk_level = "Low"
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendations": [
                "Engage qualified legal counsel",
                "Gather all relevant documentation",
                "Understand procedural requirements",
                "Consider alternative dispute resolution where applicable"
            ]
        }

enhanced_response_builder = EnhancedResponseBuilder()