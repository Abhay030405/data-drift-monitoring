"""
API Dependencies for Neural Watch
Phase 1: Data Ingestion & Quality Setup
Shared dependencies for API routes
"""
from typing import Generator
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from backend.app.utils.file_handler import FileHandler
from backend.app.utils.versioning import VersioningManager
from backend.app.utils.logger import NeuralWatchLogger

# Logger
logger = NeuralWatchLogger.get_logger("api")


# Dependency: FileHandler
def get_file_handler() -> Generator[FileHandler, None, None]:
    """
    Dependency to get FileHandler instance
    
    Yields:
        FileHandler instance
    """
    file_handler = FileHandler()
    try:
        yield file_handler
    finally:
        pass  # Cleanup if needed


# Dependency: VersioningManager
def get_versioning_manager() -> Generator[VersioningManager, None, None]:
    """
    Dependency to get VersioningManager instance
    
    Yields:
        VersioningManager instance
    """
    versioning_manager = VersioningManager()
    try:
        yield versioning_manager
    finally:
        pass  # Cleanup if needed


# Dependency: Logger
def get_logger():
    """
    Dependency to get logger instance
    
    Returns:
        Logger instance
    """
    return logger