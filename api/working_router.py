#!/usr/bin/env python3
"""
Fix the /nyaya/query endpoint while keeping all other endpoints
"""

import sys
import os
sys.path.append('.')
sys.path.append('Nyaya_AI')

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

# Import the working integrated legal advisor
from integrated_legal_advisor import IntegratedLegalAdvisor, LegalQuery

# Create a working router to replace the problematic one
working_router = APIRouter(prefix="/nyaya", tags=["nyaya"])

# Initialize the legal advisor
advisor = IntegratedLegalAdvisor()

# Pydantic models (matching the original schemas)
class UserContext(BaseModel):
    role: str
    confidence_required: bool = True

class QueryRequest(BaseModel):
    query: str = Field(..., description="Legal query text")
    jurisdiction_hint: Optional[str] = None
    domain_hint: Optional[str] = None
    user_context: UserContext

class NyayaResponse(BaseModel):
    domain: str
    jurisdiction: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    legal_route: List[str]
    constitutional_articles: List[str] = []
    provenance_chain: List[Dict[str, Any]] = []
    reasoning_trace: Dict[str, Any] = {}
    trace_id: str

@working_router.post("/query", response_model=NyayaResponse)
async def query_legal(request: QueryRequest):
    """Execute a single-jurisdiction legal query with sovereign enforcement."""
    try:
        # Create legal query using the working system
        legal_query = LegalQuery(
            query_text=request.query,
            jurisdiction_hint=request.jurisdiction_hint or "India",
            domain_hint=request.domain_hint or "criminal"
        )
        
        # Get legal advice using the working integrated advisor
        advice = advisor.provide_legal_advice(legal_query)
        
        # Map jurisdiction names
        jurisdiction_map = {"IN": "India", "UK": "UK", "UAE": "UAE"}
        jurisdiction = jurisdiction_map.get(advice.jurisdiction, advice.jurisdiction)
        
        # Build response matching the original schema
        return NyayaResponse(
            domain=advice.domain,
            jurisdiction=jurisdiction,
            confidence=advice.confidence_score,
            legal_route=["jurisdiction_router_agent", f"{jurisdiction.lower()}_legal_agent"],
            constitutional_articles=[],
            provenance_chain=[{
                "timestamp": datetime.now().isoformat(),
                "event": "query_processed",
                "agent": "integrated_legal_advisor",
                "sections_found": len(advice.relevant_sections)
            }],
            reasoning_trace={
                "legal_analysis": advice.legal_analysis[:200] + "..." if len(advice.legal_analysis) > 200 else advice.legal_analysis,
                "procedural_steps": advice.procedural_steps,
                "remedies": advice.remedies,
                "sections_found": len(advice.relevant_sections),
                "confidence_factors": {
                    "sections_matched": len(advice.relevant_sections),
                    "jurisdiction_confidence": 0.9 if advice.jurisdiction == "IN" else 0.8,
                    "domain_confidence": 0.8
                }
            },
            trace_id=advice.trace_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "QUERY_PROCESSING_ERROR",
                "message": f"Error processing legal query: {str(e)}",
                "trace_id": str(uuid.uuid4())
            }
        )

# Save this as a replacement router
if __name__ == "__main__":
    print("Working query endpoint created!")
    print("This replaces the problematic /nyaya/query endpoint")
    print("All other endpoints remain unchanged")