import re
from typing import Dict, List, Any, Optional
from procedures.loader import procedure_loader

def enrich_response(base_response: Dict[str, Any], query_text: str, domain: str, statutes: List[Dict]) -> Dict[str, Any]:
    """Enrich response with enforcement_decision, timeline, glossary, and evidence_requirements"""
    
    # Set enforcement_decision if not present
    if "enforcement_decision" not in base_response:
        base_response["enforcement_decision"] = _get_enforcement_decision(query_text)
    
    # Set timeline if not present
    if "timeline" not in base_response:
        base_response["timeline"] = _get_timeline_defaults(domain)
    
    # Set glossary if not present
    if "glossary" not in base_response:
        base_response["glossary"] = _get_glossary_defaults(statutes)
    
    # Set evidence_requirements if not present
    if "evidence_requirements" not in base_response:
        base_response["evidence_requirements"] = _get_evidence_defaults(domain)
    
    return base_response

def _get_enforcement_decision(query_text: str) -> str:
    """Determine enforcement decision based on query content"""
    query_lower = query_text.lower()
    
    # Check for suicide/self-harm keywords
    suicide_keywords = ["kill myself", "suicide", "end my life", "harm myself", "kill me"]
    if any(keyword in query_lower for keyword in suicide_keywords):
        return "ESCALATE"
    
    # Check for policy violations
    violation_keywords = ["bomb", "weapon", "violence", "illegal"]
    if any(keyword in query_lower for keyword in violation_keywords):
        return "BLOCK"
    
    return "ALLOW"

def _get_timeline_defaults(domain: str) -> List[Dict[str, str]]:
    """Get default timeline based on domain"""
    # Try to get from procedure loader first (assuming India as default)
    procedure = procedure_loader.get_procedure("india", domain.lower())
    if procedure and "procedure" in procedure and "steps" in procedure["procedure"]:
        steps = procedure["procedure"]["steps"]
        timeline = []
        for i, step in enumerate(steps[:4]):
            timeline.append({
                "step": step.get("title", f"Step {i+1}"),
                "eta": "Varies"
            })
        return timeline
    return []

def _get_glossary_defaults(statutes: List[Dict]) -> List[Dict[str, str]]:
    """Generate glossary from statutes"""
    glossary = []
    
    for statute in statutes:
        title = statute.get('title', '') if isinstance(statute, dict) else getattr(statute, 'title', '')
        act = statute.get('act', '') if isinstance(statute, dict) else getattr(statute, 'act', '')
        
        if 'Murder' in title:
            glossary.append({"term": "Murder", "definition": "Intentional killing with intent to cause death"})
        if 'Extortion' in title:
            glossary.append({"term": "Extortion", "definition": "Obtaining property by threat or force"})
        if 'Rape' in title or 'Sexual' in title:
            glossary.append({"term": "Sexual Assault", "definition": "Non-consensual sexual act"})
        if 'Theft' in title:
            glossary.append({"term": "Theft", "definition": "Dishonestly taking movable property"})
    
    return glossary

def _get_evidence_defaults(domain: str) -> List[str]:
    """Get default evidence requirements based on domain"""
    # Try to get from procedure loader first (assuming India as default)
    procedure = procedure_loader.get_procedure("india", domain.lower())
    if procedure and "procedure" in procedure and "documents_required" in procedure["procedure"]:
        return procedure["procedure"]["documents_required"][:5]
    return []
