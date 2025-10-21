"""
Centralized Logging System for Neural Watch
Phase 1: Data Ingestion & Quality Setup
"""
import logging
import sys
import io
from pathlib import Path
from datetime import datetime
from typing import Optional
import traceback

# Import settings
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from config.settings import LOG_LEVEL, LOG_FILE, LOG_DIR


class NeuralWatchLogger:
    """Custom logger for Neural Watch with structured logging"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str = "neural_watch") -> logging.Logger:
        """
        Get or create a logger instance
        
        Args:
            name: Logger name (typically module name)
            
        Returns:
            Configured logger instance
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Console handler (wrap stdout buffer with UTF-8 to avoid Windows cp1252 errors)
        try:
            # Create a UTF-8 text wrapper around the underlying buffer to ensure
            # we always write UTF-8 bytes to stdout, avoiding encode errors when
            # logging emojis or other non-cp1252 characters on Windows.
            console_stream = io.TextIOWrapper(
                sys.stdout.buffer, encoding='utf-8', write_through=True
            )
        except Exception:
            # Fallback: use sys.stdout directly if buffering/wrapper isn't available
            console_stream = sys.stdout

        console_handler = logging.StreamHandler(stream=console_stream)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger


# Convenience functions for common logging scenarios
def log_upload(filename: str, status: str, details: Optional[dict] = None):
    """Log file upload events"""
    logger = NeuralWatchLogger.get_logger("upload")
    message = f"File upload: {filename} - Status: {status}"
    if details:
        message += f" | Details: {details}"
    
    if status.lower() in ["success", "completed"]:
        logger.info(message)
    elif status.lower() in ["warning", "partial"]:
        logger.warning(message)
    else:
        logger.error(message)


def log_validation(filename: str, is_valid: bool, message: str):
    """Log validation results"""
    logger = NeuralWatchLogger.get_logger("validation")
    log_message = f"Validation: {filename} - Valid: {is_valid} - {message}"
    
    if is_valid:
        logger.info(log_message)
    else:
        logger.warning(log_message)


def log_error(error_message: str, exception: Optional[Exception] = None, 
              context: Optional[dict] = None):
    """Log errors with full traceback"""
    logger = NeuralWatchLogger.get_logger("error")
    
    log_msg = f"ERROR: {error_message}"
    if context:
        log_msg += f" | Context: {context}"
    
    logger.error(log_msg)
    
    if exception:
        logger.error(f"Exception: {str(exception)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")


def log_api_request(endpoint: str, method: str, status_code: int, 
                   response_time: Optional[float] = None):
    """Log API requests"""
    logger = NeuralWatchLogger.get_logger("api")
    message = f"API {method} {endpoint} - Status: {status_code}"
    if response_time:
        message += f" - Time: {response_time:.3f}s"
    
    if 200 <= status_code < 300:
        logger.info(message)
    elif 400 <= status_code < 500:
        logger.warning(message)
    else:
        logger.error(message)


def log_metadata(file_id: str, metadata: dict):
    """Log metadata extraction"""
    logger = NeuralWatchLogger.get_logger("metadata")
    logger.info(f"Metadata extracted for {file_id}: {metadata}")


def log_baseline_creation(version_id: str, filename: str):
    """Log baseline creation"""
    logger = NeuralWatchLogger.get_logger("baseline")
    logger.info(f"Baseline created: {version_id} from {filename}")


# Initialize default logger on module import
default_logger = NeuralWatchLogger.get_logger()
default_logger.info("="*60)
# Emoji/logging can sometimes raise encoding errors on Windows consoles using
# legacy encodings (cp1252). Wrap in try/except to ensure import-time logging
# doesn't raise and break module imports.
default_logger = NeuralWatchLogger.get_logger()
default_logger.info("="*60)
default_logger.info("Neural Watch Logging System Initialized")  # Removed emoji
default_logger.info(f"Log Level: {LOG_LEVEL}")
default_logger.info(f"Log File: {LOG_FILE}")
default_logger.info("="*60)
default_logger.info(f"Log Level: {LOG_LEVEL}")
default_logger.info(f"Log File: {LOG_FILE}")
default_logger.info("="*60)