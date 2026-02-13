"""Enhanced procedure router with legal database integration."""
from api.procedure_router import router as procedure_router
from legal_database.database_loader import legal_db
from legal_database.enhanced_response_builder import enhanced_response_builder
from fastapi import APIRouter, HTTPException, Depends
from api.dependencies import get_trace_id, validate_nonce
from typing import Dict, Any

# Add enhanced endpoints to procedure router
@procedure_router.get("/enhanced_analysis/{jurisdiction}/{domain}")
async def enhanced_legal_analysis(
    jurisdiction: str,
    domain: str,
    query: str,
    trace_id: str = Depends(get_trace_id),
    nonce: str = Depends(validate_nonce)
):
    """Get enhanced legal analysis with comprehensive database integration."""
    try:
        # Build enhanced response
        enhanced_response = enhanced_response_builder.build_enhanced_legal_response(
            query=query,
            jurisdiction=jurisdiction,
            domain_hint=domain,
            confidence=0.8,
            trace_id=trace_id
        )
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "enhanced_analysis": enhanced_response
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced analysis failed: {str(e)}"
        )

@procedure_router.get("/domain_classification/{jurisdiction}")
async def classify_query_domain(
    jurisdiction: str,
    query: str,
    trace_id: str = Depends(get_trace_id),
    nonce: str = Depends(validate_nonce)
):
    """Classify query domain using legal database."""
    try:
        classification = legal_db.classify_query_domain(query, jurisdiction)
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "classification": classification
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Domain classification failed: {str(e)}"
        )

@procedure_router.get("/legal_sections/{jurisdiction}/{domain}")
async def get_relevant_legal_sections(
    jurisdiction: str,
    domain: str,
    query: str,
    trace_id: str = Depends(get_trace_id),
    nonce: str = Depends(validate_nonce)
):
    """Get relevant legal sections from comprehensive database."""
    try:
        sections = legal_db.get_legal_sections(query, jurisdiction, domain)
        
        return {
            "status": "success",
            "trace_id": trace_id,
            "jurisdiction": jurisdiction,
            "domain": domain,
            "query": query,
            "relevant_sections": sections,
            "total_matches": len(sections)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Legal sections lookup failed: {str(e)}"
        )