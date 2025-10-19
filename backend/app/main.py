from fastapi import FastAPI
from backend.app.api.routes import data_upload  # Import your upload router

# Create FastAPI app
app = FastAPI(
    title="Intelligent Data Quality & Drift Monitoring System 3.0",
    description="Phase 1: Data Ingestion & File Handling",
    version="1.0"
)

# Include routes
app.include_router(data_upload.router, prefix="/api")
