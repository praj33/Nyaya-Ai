from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.router import router
import uvicorn
import os

# Create FastAPI app
app = FastAPI(
    title="Nyaya Legal AI API Gateway",
    description="Sovereign-compliant API gateway for multi-agent legal intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from api.response_builder import ResponseBuilder
    trace_id = getattr(request.state, 'trace_id', 'unknown')
    return HTTPException(
        status_code=500,
        detail=ResponseBuilder.build_error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred",
            trace_id
        ).dict()
    )

# Middleware to add trace_id to request state
@app.middleware("http")
async def add_trace_id_middleware(request: Request, call_next):
    import uuid
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id
    response = await call_next(request)
    return response

# Include routers
app.include_router(router)

# Include debug router (for development only)
try:
    from api.debug_router import debug_router
    app.include_router(debug_router)
except ImportError:
    pass  # Debug router not available

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "nyaya-api-gateway"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Nyaya Legal AI API Gateway",
        "version": "1.0.0",
        "description": "Sovereign-compliant multi-agent legal intelligence platform",
        "endpoints": {
            "query": "POST /nyaya/query",
            "multi_jurisdiction": "POST /nyaya/multi_jurisdiction",
            "explain_reasoning": "POST /nyaya/explain_reasoning",
            "feedback": "POST /nyaya/feedback",
            "trace": "GET /nyaya/trace/{trace_id}",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }

if __name__ == "__main__":
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )