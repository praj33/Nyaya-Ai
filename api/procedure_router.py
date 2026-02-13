"""Procedure API router for legal procedure intelligence."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from api.schemas import (
    ProcedureRequest, ProcedureResponse, EvidenceAssessmentRequest,
    EvidenceAssessmentResponse, FailureAnalysisRequest, FailureAnalysisResponse,
    ProcedureComparisonRequest, ProcedureComparisonResponse
)
from api.dependencies import get_trace_id
from api.response_builder import ResponseBuilder
from procedures.intelligence import procedure_intelligence
from procedures.loader import procedure_loader

procedure_router = APIRouter(prefix="/nyaya/procedures", tags=["procedures"])


@procedure_router.post("/analyze", response_model=ProcedureResponse)
async def analyze_procedure(
    request: ProcedureRequest,
    trace_id: str = Depends(get_trace_id)
):
    """Analyze a legal procedure for a specific country and domain."""
    try:
        analysis = procedure_intelligence.analyze_procedure(
            country=request.country,
            domain=request.domain,
            current_step=request.current_step
        )
        
        if "error" in analysis:
            raise HTTPException(
                status_code=404,
                detail=ResponseBuilder.build_error_response(
                    "PROCEDURE_NOT_FOUND",
                    analysis["error"],
                    trace_id
                ).dict()
            )
        
        return ProcedureResponse(**analysis)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ResponseBuilder.build_error_response(
                "INTERNAL_ERROR",
                f"Failed to analyze procedure: {str(e)}",
                trace_id
            ).dict()
        )


@procedure_router.get("/summary/{country}/{domain}")
async def get_procedure_summary(
    country: str,
    domain: str,
    trace_id: str = Depends(get_trace_id)
):
    """Get a summary of a legal procedure."""
    try:
        summary = procedure_intelligence.get_procedure_summary(country, domain)
        
        if "error" in summary:
            raise HTTPException(
                status_code=404,
                detail=ResponseBuilder.build_error_response(
                    "PROCEDURE_NOT_FOUND",
                    summary["error"],
                    trace_id
                ).dict()
            )
        
        return summary
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ResponseBuilder.build_error_response(
                "INTERNAL_ERROR",
                f"Failed to get procedure summary: {str(e)}",
                trace_id
            ).dict()
        )


@procedure_router.post("/evidence/assess", response_model=EvidenceAssessmentResponse)
async def assess_evidence(
    request: EvidenceAssessmentRequest,
    trace_id: str = Depends(get_trace_id)
):
    """Assess evidence readiness for a given procedural step."""
    try:
        assessment = procedure_intelligence.assess_evidence_readiness(
            canonical_step=request.canonical_step,
            available_documents=request.available_documents
        )
        
        return EvidenceAssessmentResponse(**assessment)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ResponseBuilder.build_error_response(
                "INTERNAL_ERROR",
                f"Failed to assess evidence: {str(e)}",
                trace_id
            ).dict()
        )


@procedure_router.post("/failure/analyze", response_model=FailureAnalysisResponse)
async def analyze_failure(
    request: FailureAnalysisRequest,
    trace_id: str = Depends(get_trace_id)
):
    """Analyze failure risk for a given failure code."""
    try:
        analysis = procedure_intelligence.analyze_failure_risk(request.failure_code)
        
        if "error" in analysis:
            raise HTTPException(
                status_code=404,
                detail=ResponseBuilder.build_error_response(
                    "FAILURE_CODE_NOT_FOUND",
                    analysis["error"],
                    trace_id
                ).dict()
            )
        
        return FailureAnalysisResponse(**analysis)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ResponseBuilder.build_error_response(
                "INTERNAL_ERROR",
                f"Failed to analyze failure: {str(e)}",
                trace_id
            ).dict()
        )


@procedure_router.post("/compare", response_model=ProcedureComparisonResponse)
async def compare_procedures(
    request: ProcedureComparisonRequest,
    trace_id: str = Depends(get_trace_id)
):
    """Compare procedures across multiple countries for the same domain."""
    try:
        comparison = procedure_intelligence.compare_procedures(
            countries=request.countries,
            domain=request.domain
        )
        
        return ProcedureComparisonResponse(**comparison)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ResponseBuilder.build_error_response(
                "INTERNAL_ERROR",
                f"Failed to compare procedures: {str(e)}",
                trace_id
            ).dict()
        )


@procedure_router.get("/list")
async def list_procedures(trace_id: str = Depends(get_trace_id)):
    """List all available procedures by country and domain."""
    try:
        procedures = procedure_loader.list_available_procedures()
        return {
            "available_procedures": procedures,
            "total_countries": len(procedures),
            "trace_id": trace_id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ResponseBuilder.build_error_response(
                "INTERNAL_ERROR",
                f"Failed to list procedures: {str(e)}",
                trace_id
            ).dict()
        )


@procedure_router.get("/schemas")
async def get_schemas(trace_id: str = Depends(get_trace_id)):
    """Get all available schemas."""
    try:
        return {
            "canonical_taxonomy": procedure_loader.get_canonical_taxonomy(),
            "evidence_readiness": procedure_loader.get_evidence_readiness(),
            "failure_paths": procedure_loader.get_failure_paths(),
            "system_compliance": procedure_loader.get_system_compliance(),
            "trace_id": trace_id
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ResponseBuilder.build_error_response(
                "INTERNAL_ERROR",
                f"Failed to get schemas: {str(e)}",
                trace_id
            ).dict()
        )
