"""
Neural Watch - FastAPI Main Application
Phase 1: Data Ingestion & Quality Setup
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config.settings import (
    API_TITLE, API_DESCRIPTION, API_VERSION, API_DOCS_URL, 
    API_REDOC_URL, CORS_ORIGINS, BACKEND_PORT, DEBUG_MODE
)
from backend.app.api.routes import data_upload
from backend.app.utils.logger import NeuralWatchLogger

# Initialize logger
logger = NeuralWatchLogger.get_logger("main")

# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url=API_DOCS_URL,
    redoc_url=API_REDOC_URL
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(data_upload.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("="*60)
    logger.info(f"{API_TITLE} v{API_VERSION} - Starting Up")  # Removed emoji
    logger.info("="*60)
    logger.info(f"Environment: {'Development' if DEBUG_MODE else 'Production'}")
    logger.info(f"API Docs: http://localhost:{BACKEND_PORT}{API_DOCS_URL}")
    logger.info(f"CORS Origins: {', '.join(CORS_ORIGINS)}")
    logger.info("="*60)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("="*60)
    logger.info(f"{API_TITLE} - Shutting Down")  # Removed emoji
    logger.info("="*60)
    
# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint
    
    Returns:
        JSON response with system status
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": API_TITLE,
        "version": API_VERSION,
        "phase": "1 - Data Ingestion & Quality Setup"
    }, status_code=200)

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information
    
    Returns:
        JSON response with API details
    """
    return JSONResponse(content={
        "message": f"Welcome to {API_TITLE}",
        "version": API_VERSION,
        "description": API_DESCRIPTION,
        "docs": f"{API_DOCS_URL}",
        "health": "/health",
        "endpoints": {
            "upload": "/api/v1/upload_data",
            "list_uploads": "/api/v1/list_uploads",
            "file_metadata": "/api/v1/get_file_metadata/{file_id}",
            "delete_upload": "/api/v1/delete_upload/{file_id}",
            "list_baselines": "/api/v1/list_baselines",
            "get_baseline": "/api/v1/get_baseline/{version_id}"
        }
    }, status_code=200)


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on http://0.0.0.0:{BACKEND_PORT}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=DEBUG_MODE,
        log_level="info"
    )