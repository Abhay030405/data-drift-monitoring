"""
Global Configuration Settings for Neural Watch
Phase 1: Data Ingestion & Quality Setup
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Application Settings
APP_NAME = os.getenv("APP_NAME", "Neural Watch")
APP_VERSION = os.getenv("APP_VERSION", "3.0")
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# API Configuration
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", 8501))
BACKEND_URL = f"http://localhost:{BACKEND_PORT}"

# File Upload Settings
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 500))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_FORMATS = os.getenv("ALLOWED_FORMATS", "csv,json,parquet").split(",")

# Directory Paths
DATA_RAW_PATH = BASE_DIR / os.getenv("DATA_RAW_PATH", "data/raw")
DATA_BASELINE_PATH = BASE_DIR / os.getenv("DATA_BASELINE_PATH", "data/baseline")
DATA_PROCESSED_PATH = BASE_DIR / os.getenv("DATA_PROCESSED_PATH", "data/processed")
DRIFT_REPORTS_PATH = BASE_DIR / os.getenv("DRIFT_REPORTS_PATH", "data/drift_reports")

# Create directories if they don't exist
for path in [DATA_RAW_PATH, DATA_BASELINE_PATH, DATA_PROCESSED_PATH, DRIFT_REPORTS_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "neural_watch.log"

# CORS Settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")

# Database Configuration (for future phases)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./neural_watch.db")

# Validation Thresholds (Phase 1)
class ValidationThresholds:
    """Thresholds for data validation"""
    MIN_ROWS = 10  # Minimum rows required in dataset
    MIN_COLUMNS = 1  # Minimum columns required
    MAX_MISSING_PERCENTAGE = 100  # Maximum allowed missing percentage per column (warn only)
    WARN_MISSING_PERCENTAGE = 50  # Warning threshold for missing values

# File Naming Patterns
FILE_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
BASELINE_VERSION_PREFIX = "baseline_v"

# API Settings
API_TITLE = f"{APP_NAME} API"
API_DESCRIPTION = "Intelligent Data Quality & Drift Monitoring System"
API_VERSION = APP_VERSION
API_DOCS_URL = "/docs"
API_REDOC_URL = "/redoc"

# Security (for future phases)
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "change-this-in-production")

# Phase-specific feature flags
FEATURES = {
    "phase_1_ingestion": True,
    "phase_2_quality_checks": True,
    "phase_3_drift_detection": False,
    "phase_4_llm_reasoning": False,
    "phase_5_model_monitoring": False,
    "streaming_enabled": False,
}

# Print configuration on import (only in debug mode)
if DEBUG_MODE:
    print(f"{'='*60}")
    print(f"🧠 {APP_NAME} v{APP_VERSION} - Configuration Loaded")
    print(f"{'='*60}")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Backend: {BACKEND_HOST}:{BACKEND_PORT}")
    print(f"Max File Size: {MAX_FILE_SIZE_MB}MB")
    print(f"Allowed Formats: {', '.join(ALLOWED_FORMATS)}")
    print(f"Data Paths Created: ✓")
    print(f"{'='*60}\n")