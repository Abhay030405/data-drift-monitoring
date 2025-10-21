"""
File Handler Module for Neural Watch
Phase 1: Data Ingestion & Quality Setup
Handles CSV, JSON, and Parquet file operations with validation
"""
import os
import hashlib
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from datetime import datetime
import pandas as pd
import json

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from config.settings import (
    DATA_RAW_PATH, DATA_BASELINE_PATH, ALLOWED_FORMATS,
    MAX_FILE_SIZE_BYTES, FILE_TIMESTAMP_FORMAT, ValidationThresholds
)
from backend.app.utils.logger import (
    NeuralWatchLogger, log_validation, log_error, log_metadata
)

logger = NeuralWatchLogger.get_logger("file_handler")


class FileHandler:
    """Handle file uploads, validation, and metadata extraction"""
    
    def __init__(self):
        """Initialize file handler and create necessary directories"""
        self.raw_path = DATA_RAW_PATH
        self.baseline_path = DATA_BASELINE_PATH
        self.supported_formats = ALLOWED_FORMATS
        self.max_file_size = MAX_FILE_SIZE_BYTES
        
        # Ensure directories exist
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.baseline_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileHandler initialized | Raw: {self.raw_path} | Baseline: {self.baseline_path}")
    
    def validate_file_format(self, filename: str) -> Tuple[bool, str]:
        """
        Validate if file format is supported
        
        Args:
            filename: Name of the uploaded file
            
        Returns:
            Tuple of (is_valid, message)
        """
        extension = filename.split('.')[-1].lower()
        if extension not in self.supported_formats:
            message = f"Unsupported format '{extension}'. Supported: {', '.join(self.supported_formats)}"
            log_validation(filename, False, message)
            return False, message
        
        log_validation(filename, True, f"Format '{extension}' is valid")
        return True, f"Valid format: {extension}"
    
    def validate_file_size(self, file_path: Path) -> Tuple[bool, str]:
        """
        Validate file size against maximum allowed
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, message)
        """
        file_size = file_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        
        if file_size > self.max_file_size:
            message = f"File too large: {size_mb:.2f}MB (max: {self.max_file_size / (1024 * 1024)}MB)"
            log_validation(file_path.name, False, message)
            return False, message
        
        log_validation(file_path.name, True, f"File size OK: {size_mb:.2f}MB")
        return True, f"File size: {size_mb:.2f}MB"
    
    def compute_file_hash(self, file_path: Path) -> str:
        """
        Compute SHA-256 hash of file for deduplication
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal hash string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        file_hash = sha256_hash.hexdigest()[:16]  # First 16 chars
        logger.debug(f"Computed hash for {file_path.name}: {file_hash}")
        return file_hash
    
    def read_file(self, file_path: Path) -> Tuple[Optional[pd.DataFrame], str]:
        """
        Read file into pandas DataFrame based on extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (DataFrame or None, error_message)
        """
        try:
            extension = file_path.suffix.lower().replace('.', '')
            
            logger.info(f"Reading file: {file_path.name} (format: {extension})")
            
            if extension == 'csv':
                df = pd.read_csv(file_path)
            elif extension == 'json':
                df = pd.read_json(file_path)
            elif extension == 'parquet':
                df = pd.read_parquet(file_path)
            else:
                error_msg = f"Unsupported file format: {extension}"
                log_error(error_msg)
                return None, error_msg
            
            logger.info(f"Successfully read {file_path.name}: {len(df)} rows, {len(df.columns)} columns")
            return df, ""
            
        except Exception as e:
            error_msg = f"Error reading file {file_path.name}: {str(e)}"
            log_error(error_msg, exception=e)
            return None, error_msg
    
    def validate_dataframe(
        self, 
        df: pd.DataFrame, 
        filename: str,
        expected_columns: Optional[List[str]] = None,
        expected_dtypes: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Validate DataFrame structure and content
        
        Args:
            df: DataFrame to validate
            filename: Original filename for logging
            expected_columns: List of expected column names (optional)
            expected_dtypes: Dict of column:dtype pairs (optional)
            
        Returns:
            Tuple of (is_valid, message, validation_report)
        """
        validation_report = {
            "filename": filename,
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "checks_passed": []
        }
        
        # Check 1: Minimum rows
        if len(df) < ValidationThresholds.MIN_ROWS:
            validation_report["errors"].append(
                f"Insufficient rows: {len(df)} (minimum: {ValidationThresholds.MIN_ROWS})"
            )
            validation_report["is_valid"] = False
        else:
            validation_report["checks_passed"].append(f"Row count OK: {len(df)} rows")
        
        # Check 2: Minimum columns
        if len(df.columns) < ValidationThresholds.MIN_COLUMNS:
            validation_report["errors"].append(
                f"Insufficient columns: {len(df.columns)} (minimum: {ValidationThresholds.MIN_COLUMNS})"
            )
            validation_report["is_valid"] = False
        else:
            validation_report["checks_passed"].append(f"Column count OK: {len(df.columns)} columns")
        
        # Check 3: Empty DataFrame
        if df.empty:
            validation_report["errors"].append("DataFrame is empty")
            validation_report["is_valid"] = False
        else:
            validation_report["checks_passed"].append("DataFrame is not empty")
        
        # Check 4: All-null columns
        null_columns = df.columns[df.isnull().all()].tolist()
        if null_columns:
            validation_report["warnings"].append(
                f"Columns with all null values: {', '.join(null_columns)}"
            )
        
        # Check 5: High missing percentage
        missing_pct = (df.isnull().sum() / len(df) * 100).to_dict()
        high_missing_cols = [
            col for col, pct in missing_pct.items() 
            if pct > ValidationThresholds.WARN_MISSING_PERCENTAGE
        ]
        if high_missing_cols:
            validation_report["warnings"].append(
                f"Columns with >{ValidationThresholds.WARN_MISSING_PERCENTAGE}% missing: {', '.join(high_missing_cols)}"
            )
        
        # Check 6: Expected columns (if baseline exists)
        if expected_columns is not None:
            missing_cols = set(expected_columns) - set(df.columns)
            extra_cols = set(df.columns) - set(expected_columns)
            
            if missing_cols:
                validation_report["warnings"].append(
                    f"Missing expected columns: {', '.join(missing_cols)}"
                )
            if extra_cols:
                validation_report["warnings"].append(
                    f"Extra columns not in baseline: {', '.join(extra_cols)}"
                )
            if not missing_cols and not extra_cols:
                validation_report["checks_passed"].append("Column schema matches baseline")
        
        # Check 7: Data types (if expected dtypes provided)
        if expected_dtypes is not None:
            dtype_mismatches = []
            for col, expected_dtype in expected_dtypes.items():
                if col in df.columns:
                    actual_dtype = str(df[col].dtype)
                    if actual_dtype != expected_dtype:
                        dtype_mismatches.append(
                            f"{col}: expected {expected_dtype}, got {actual_dtype}"
                        )
            if dtype_mismatches:
                validation_report["warnings"].append(
                    f"Data type mismatches: {'; '.join(dtype_mismatches)}"
                )
        
        # Construct summary message
        if validation_report["is_valid"]:
            message = f"Validation passed with {len(validation_report['warnings'])} warning(s)"
        else:
            message = f"Validation failed: {'; '.join(validation_report['errors'])}"
        
        log_validation(filename, validation_report["is_valid"], message)
        
        return validation_report["is_valid"], message, validation_report
    
    def compute_metadata(self, df: pd.DataFrame, filename: str, file_path: Path) -> Dict:
        """
        Compute comprehensive metadata for the dataset
        
        Args:
            df: DataFrame to analyze
            filename: Original filename
            file_path: Path to the file
            
        Returns:
            Dictionary containing metadata
        """
        try:
            # Basic metadata
            metadata = {
                "filename": filename,
                "file_path": str(file_path),
                "timestamp": datetime.now().isoformat(),
                "file_size_bytes": file_path.stat().st_size,
                "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                "file_hash": self.compute_file_hash(file_path),
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
            }
            
            # Missing value analysis
            missing_counts = df.isnull().sum().to_dict()
            missing_percentages = (df.isnull().sum() / len(df) * 100).round(2).to_dict()
            
            metadata["missing_values"] = {
                "counts": missing_counts,
                "percentages": missing_percentages,
                "total_missing": int(df.isnull().sum().sum()),
                "columns_with_missing": [
                    col for col, count in missing_counts.items() if count > 0
                ]
            }
            
            # Numeric column statistics
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                metadata["numeric_summary"] = {
                    col: {
                        "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                        "std": float(df[col].std()) if not df[col].isnull().all() else None,
                        "min": float(df[col].min()) if not df[col].isnull().all() else None,
                        "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    }
                    for col in numeric_cols[:10]  # Limit to first 10 numeric columns
                }
            
            # Categorical column info
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            if categorical_cols:
                metadata["categorical_summary"] = {
                    col: {
                        "unique_values": int(df[col].nunique()),
                        "top_values": df[col].value_counts().head(5).to_dict()
                    }
                    for col in categorical_cols[:10]  # Limit to first 10 categorical columns
                }
            
            # Duplicate rows
            duplicate_count = df.duplicated().sum()
            metadata["duplicates"] = {
                "count": int(duplicate_count),
                "percentage": round(duplicate_count / len(df) * 100, 2)
            }
            
            log_metadata(file_path.name, metadata)
            return metadata
            
        except Exception as e:
            log_error(f"Error computing metadata for {filename}", exception=e)
            return {"error": str(e)}
    
    def save_file(self, df: pd.DataFrame, destination: Path, filename: str) -> Tuple[bool, str, Path]:
        """
        Save DataFrame to specified destination
        
        Args:
            df: DataFrame to save
            destination: Target directory
            filename: Desired filename
            
        Returns:
            Tuple of (success, message, saved_path)
        """
        try:
            destination.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime(FILE_TIMESTAMP_FORMAT)
            name, ext = os.path.splitext(filename)
            new_filename = f"{name}_{timestamp}{ext}"
            save_path = destination / new_filename
            
            # Save based on extension
            extension = ext.lower().replace('.', '')
            if extension == 'csv':
                df.to_csv(save_path, index=False)
            elif extension == 'json':
                df.to_json(save_path, orient='records', indent=2)
            elif extension == 'parquet':
                df.to_parquet(save_path, index=False)
            else:
                return False, f"Unsupported format for saving: {extension}", save_path
            
            logger.info(f"File saved successfully: {save_path}")
            return True, f"File saved as {new_filename}", save_path
            
        except Exception as e:
            error_msg = f"Error saving file: {str(e)}"
            log_error(error_msg, exception=e)
            return False, error_msg, Path()
    
    def check_duplicate_file(self, file_hash: str, exclude_path: Optional[Path] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if file with same hash already exists
        
        Args:
            file_hash: Hash of the file to check
            exclude_path: Path to exclude from search (e.g., temp file)
            
        Returns:
            Tuple of (is_duplicate, existing_file_path)
        """
        # Search in raw data directory
        for existing_file in self.raw_path.glob('*'):
            if existing_file.is_file():
                # Skip temp files and excluded paths
                if existing_file.name.startswith('temp_'):
                    continue
                if exclude_path and existing_file == exclude_path:
                    continue
                    
                try:
                    existing_hash = self.compute_file_hash(existing_file)
                    if existing_hash == file_hash:
                        logger.warning(f"Duplicate file detected: {existing_file.name}")
                        return True, str(existing_file)
                except Exception:
                    continue
        
        return False, None


# Convenience function to get FileHandler instance
def get_file_handler() -> FileHandler:
    """Get FileHandler singleton instance"""
    return FileHandler()