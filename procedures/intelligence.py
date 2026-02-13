"""Procedure intelligence for legal procedure analysis."""
from typing import Dict, Any, List, Optional
from procedures.loader import procedure_loader


class ProcedureIntelligence:
    """Provides intelligent analysis of legal procedures."""
    
    def __init__(self):
        self.loader = procedure_loader
    
    def analyze_procedure(self, country: str, domain: str, current_step: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a legal procedure and provide intelligence."""
        procedure = self.loader.get_procedure(country, domain)
        if not procedure:
            return {"error": f"Procedure not found for {country}/{domain}"}
        
        analysis = {
            "country": country,
            "domain": domain,
            "procedure_overview": {
                "authorities": procedure.get("procedure", {}).get("authority", []),
                "total_steps": len(procedure.get("procedure", {}).get("steps", [])),
                "timelines": procedure.get("procedure", {}).get("timelines", {}),
                "documents_required": procedure.get("procedure", {}).get("documents_required", [])
            },
            "steps": procedure.get("procedure", {}).get("steps", []),
            "escalation_paths": procedure.get("procedure", {}).get("escalation_paths", [])
        }
        
        if current_step:
            step_info = self.loader.get_step_by_canonical(country, domain, current_step)
            if step_info:
                analysis["current_step_analysis"] = self._analyze_step(step_info)
        
        return analysis
    
    def _analyze_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a specific procedure step."""
        return {
            "step_number": step.get("step"),
            "title": step.get("title"),
            "canonical_step": step.get("canonical_step"),
            "description": step.get("description"),
            "actor": step.get("actor"),
            "conditional_branches": step.get("conditional_branches", []),
            "outcome_intelligence": step.get("outcome_intelligence", {}),
            "cost_effort": step.get("cost_effort", {}),
            "risk_flags": step.get("risk_flags", {})
        }
    
    def get_next_steps(self, country: str, domain: str, current_step: str, outcome: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get possible next steps based on current step and outcome."""
        step = self.loader.get_step_by_canonical(country, domain, current_step)
        if not step:
            return []
        
        next_steps = []
        
        # Check conditional branches
        if outcome and "conditional_branches" in step:
            for branch in step["conditional_branches"]:
                if branch.get("canonical_outcome") == outcome:
                    next_steps.append({
                        "next_step": branch.get("next_step"),
                        "effect": branch.get("effect"),
                        "outcome": outcome
                    })
        
        # If no specific outcome, return all possible branches
        if not next_steps and "conditional_branches" in step:
            for branch in step["conditional_branches"]:
                next_steps.append({
                    "next_step": branch.get("next_step"),
                    "effect": branch.get("effect"),
                    "outcome": branch.get("canonical_outcome")
                })
        
        return next_steps
    
    def assess_evidence_readiness(self, canonical_step: str, available_documents: List[str]) -> Dict[str, Any]:
        """Assess evidence readiness for a given step."""
        evidence_schema = self.loader.get_evidence_readiness()
        mandatory_docs = evidence_schema.get("mandatory_documents_by_step", {}).get(canonical_step, [])
        
        missing_docs = [doc for doc in mandatory_docs if doc not in available_documents]
        
        if not missing_docs:
            state = "EVIDENCE_COMPLETE"
        elif len(missing_docs) < len(mandatory_docs):
            state = "EVIDENCE_PARTIAL"
        else:
            state = "EVIDENCE_MISSING"
        
        penalty = self.loader.calculate_evidence_penalty(state)
        
        return {
            "evidence_state": state,
            "mandatory_documents": mandatory_docs,
            "available_documents": available_documents,
            "missing_documents": missing_docs,
            "confidence_penalty": penalty,
            "readiness_percentage": ((len(mandatory_docs) - len(missing_docs)) / len(mandatory_docs) * 100) if mandatory_docs else 100
        }
    
    def analyze_failure_risk(self, failure_code: str) -> Dict[str, Any]:
        """Analyze failure risk for a given failure code."""
        failure_info = self.loader.get_failure_info(failure_code)
        if not failure_info:
            return {"error": f"Failure code {failure_code} not found"}
        
        return {
            "failure_code": failure_code,
            "failure_type": failure_info.get("failure_type"),
            "description": failure_info.get("description"),
            "recoverable": failure_info.get("recoverable"),
            "severity": "High" if not failure_info.get("recoverable") else "Medium"
        }
    
    def get_procedure_summary(self, country: str, domain: str) -> Dict[str, Any]:
        """Get a summary of a legal procedure."""
        procedure = self.loader.get_procedure(country, domain)
        if not procedure:
            return {"error": f"Procedure not found for {country}/{domain}"}
        
        steps = procedure.get("procedure", {}).get("steps", [])
        
        return {
            "country": country,
            "domain": domain,
            "last_verified": procedure.get("last_verified"),
            "total_steps": len(steps),
            "authorities": procedure.get("procedure", {}).get("authority", []),
            "timelines": procedure.get("procedure", {}).get("timelines", {}),
            "key_steps": [
                {
                    "step": s.get("step"),
                    "title": s.get("title"),
                    "canonical_step": s.get("canonical_step")
                }
                for s in steps
            ],
            "sources": procedure.get("sources", [])
        }
    
    def compare_procedures(self, countries: List[str], domain: str) -> Dict[str, Any]:
        """Compare procedures across multiple countries for the same domain."""
        comparison = {
            "domain": domain,
            "countries": countries,
            "procedures": {}
        }
        
        for country in countries:
            summary = self.get_procedure_summary(country, domain)
            if "error" not in summary:
                comparison["procedures"][country] = summary
        
        return comparison


# Global instance
procedure_intelligence = ProcedureIntelligence()
