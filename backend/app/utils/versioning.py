"""
Versioning Manager for Neural Watch
Phase 1: Data Ingestion & Quality Setup
Handles baseline versioning and metadata tracking
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import shutil
import pandas as pd

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from config.settings import (
    DATA_BASELINE_PATH, BASELINE_VERSION_PREFIX, FILE_TIMESTAMP_FORMAT
)
from backend.app.utils.logger import (
    NeuralWatchLogger, log_baseline_creation, log_error
)

logger = NeuralWatchLogger.get_logger("versioning")


class VersioningManager:
    """Manage baseline versions and dataset metadata"""
    
    def __init__(self):
        """Initialize versioning manager"""
        self.baseline_path = DATA_BASELINE_PATH
        self.baseline_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"VersioningManager initialized | Path: {self.baseline_path}")
    
    def get_next_version_number(self) -> int:
        """
        Get the next available version number
        
        Returns:
            Next version number as integer
        """
        existing_versions = self.list_baseline_versions()
        if not existing_versions:
            return 1
        
        version_numbers = []
        for version in existing_versions:
            try:
                # Extract version number from version_id
                # Format: baseline_v1_20250421
                version_num = int(version['version_id'].split('_')[1].replace('v', ''))
                version_numbers.append(version_num)
            except (ValueError, IndexError):
                continue
        
        return max(version_numbers, default=0) + 1
    
    def create_baseline_version(
        self, 
        source_file_path: Path, 
        metadata: Dict,
        description: Optional[str] = None
    ) -> Tuple[bool, str, Dict]:
        """
        Create a new baseline version from uploaded dataset
        
        Args:
            source_file_path: Path to the source file
            metadata: Metadata dictionary for the dataset
            description: Optional description for this baseline
            
        Returns:
            Tuple of (success, message, baseline_info)
        """
        try:
            # Generate version ID
            version_number = self.get_next_version_number()
            date_str = datetime.now().strftime("%Y%m%d")
            version_id = f"{BASELINE_VERSION_PREFIX}{version_number}_{date_str}"
            
            # Create baseline filename
            extension = source_file_path.suffix
            baseline_filename = f"{version_id}{extension}"
            baseline_path = self.baseline_path / baseline_filename
            
            # Copy file to baseline directory
            shutil.copy2(source_file_path, baseline_path)
            logger.info(f"Baseline file copied: {baseline_path}")
            
            # Create baseline metadata
            baseline_info = {
                "version_id": version_id,
                "version_number": version_number,
                "created_at": datetime.now().isoformat(),
                "original_filename": source_file_path.name,
                "baseline_filename": baseline_filename,
                "baseline_path": str(baseline_path),
                "description": description or f"Baseline version {version_number}",
                "source_metadata": metadata
            }
            
            # Save metadata JSON
            metadata_filename = f"{version_id}_metadata.json"
            metadata_path = self.baseline_path / metadata_filename
            
            with open(metadata_path, 'w') as f:
                json.dump(baseline_info, f, indent=2)
            
            logger.info(f"Baseline metadata saved: {metadata_path}")
            log_baseline_creation(version_id, source_file_path.name)
            
            return True, f"Baseline {version_id} created successfully", baseline_info
            
        except Exception as e:
            error_msg = f"Error creating baseline version: {str(e)}"
            log_error(error_msg, exception=e)
            return False, error_msg, {}
    
    def get_latest_baseline(self) -> Optional[Dict]:
        """
        Get the most recent baseline version
        
        Returns:
            Baseline info dictionary or None if no baselines exist
        """
        versions = self.list_baseline_versions()
        if not versions:
            logger.warning("No baseline versions found")
            return None
        
        # Sort by version number (descending)
        sorted_versions = sorted(
            versions, 
            key=lambda x: x.get('version_number', 0), 
            reverse=True
        )
        
        latest = sorted_versions[0]
        logger.info(f"Latest baseline: {latest['version_id']}")
        return latest
    
    def get_baseline_by_version(self, version_id: str) -> Optional[Dict]:
        """
        Get baseline info for a specific version
        
        Args:
            version_id: Version identifier (e.g., 'baseline_v1_20250421')
            
        Returns:
            Baseline info dictionary or None if not found
        """
        metadata_path = self.baseline_path / f"{version_id}_metadata.json"
        
        if not metadata_path.exists():
            logger.warning(f"Baseline version not found: {version_id}")
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                baseline_info = json.load(f)
            
            logger.info(f"Loaded baseline: {version_id}")
            return baseline_info
            
        except Exception as e:
            log_error(f"Error loading baseline {version_id}", exception=e)
            return None
    
    def list_baseline_versions(self) -> List[Dict]:
        """
        List all available baseline versions
        
        Returns:
            List of baseline info dictionaries
        """
        baselines = []
        
        # Find all metadata JSON files
        for metadata_file in self.baseline_path.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r') as f:
                    baseline_info = json.load(f)
                    baselines.append(baseline_info)
            except Exception as e:
                logger.warning(f"Error reading metadata file {metadata_file}: {str(e)}")
                continue
        
        # Sort by creation date (newest first)
        baselines.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        logger.info(f"Found {len(baselines)} baseline version(s)")
        return baselines
    
    def load_baseline_dataframe(self, version_id: str) -> Tuple[Optional[pd.DataFrame], str]:
        """
        Load baseline dataset as DataFrame
        
        Args:
            version_id: Version identifier
            
        Returns:
            Tuple of (DataFrame or None, error_message)
        """
        baseline_info = self.get_baseline_by_version(version_id)
        
        if not baseline_info:
            return None, f"Baseline version {version_id} not found"
        
        baseline_path = Path(baseline_info['baseline_path'])
        
        if not baseline_path.exists():
            error_msg = f"Baseline file not found: {baseline_path}"
            log_error(error_msg)
            return None, error_msg
        
        try:
            # Read based on file extension
            extension = baseline_path.suffix.lower().replace('.', '')
            
            if extension == 'csv':
                df = pd.read_csv(baseline_path)
            elif extension == 'json':
                df = pd.read_json(baseline_path)
            elif extension == 'parquet':
                df = pd.read_parquet(baseline_path)
            else:
                return None, f"Unsupported baseline format: {extension}"
            
            logger.info(f"Loaded baseline {version_id}: {len(df)} rows, {len(df.columns)} columns")
            return df, ""
            
        except Exception as e:
            error_msg = f"Error loading baseline {version_id}: {str(e)}"
            log_error(error_msg, exception=e)
            return None, error_msg
    
    def delete_baseline_version(self, version_id: str) -> Tuple[bool, str]:
        """
        Delete a baseline version (use with caution!)
        
        Args:
            version_id: Version identifier to delete
            
        Returns:
            Tuple of (success, message)
        """
        baseline_info = self.get_baseline_by_version(version_id)
        
        if not baseline_info:
            return False, f"Baseline version {version_id} not found"
        
        try:
            # Delete baseline file
            baseline_path = Path(baseline_info['baseline_path'])
            if baseline_path.exists():
                baseline_path.unlink()
                logger.info(f"Deleted baseline file: {baseline_path}")
            
            # Delete metadata file
            metadata_path = self.baseline_path / f"{version_id}_metadata.json"
            if metadata_path.exists():
                metadata_path.unlink()
                logger.info(f"Deleted metadata file: {metadata_path}")
            
            return True, f"Baseline {version_id} deleted successfully"
            
        except Exception as e:
            error_msg = f"Error deleting baseline {version_id}: {str(e)}"
            log_error(error_msg, exception=e)
            return False, error_msg
    
    def compare_with_baseline(
        self, 
        current_metadata: Dict, 
        baseline_version_id: Optional[str] = None
    ) -> Dict:
        """
        Compare current dataset metadata with baseline
        
        Args:
            current_metadata: Metadata of current dataset
            baseline_version_id: Specific baseline version (uses latest if None)
            
        Returns:
            Comparison report dictionary
        """
        # Get baseline
        if baseline_version_id:
            baseline_info = self.get_baseline_by_version(baseline_version_id)
        else:
            baseline_info = self.get_latest_baseline()
        
        if not baseline_info:
            return {
                "has_baseline": False,
                "message": "No baseline available for comparison"
            }
        
        baseline_metadata = baseline_info['source_metadata']
        
        comparison = {
            "has_baseline": True,
            "baseline_version": baseline_info['version_id'],
            "comparison_timestamp": datetime.now().isoformat(),
            "differences": []
        }
        
        # Compare row counts
        current_rows = current_metadata.get('rows', 0)
        baseline_rows = baseline_metadata.get('rows', 0)
        if current_rows != baseline_rows:
            comparison["differences"].append({
                "field": "rows",
                "baseline": baseline_rows,
                "current": current_rows,
                "change": current_rows - baseline_rows,
                "change_percentage": round((current_rows - baseline_rows) / baseline_rows * 100, 2) if baseline_rows > 0 else None
            })
        
        # Compare column counts
        current_cols = current_metadata.get('columns', 0)
        baseline_cols = baseline_metadata.get('columns', 0)
        if current_cols != baseline_cols:
            comparison["differences"].append({
                "field": "columns",
                "baseline": baseline_cols,
                "current": current_cols,
                "change": current_cols - baseline_cols
            })
        
        # Compare column names
        current_col_names = set(current_metadata.get('column_names', []))
        baseline_col_names = set(baseline_metadata.get('column_names', []))
        
        missing_cols = baseline_col_names - current_col_names
        extra_cols = current_col_names - baseline_col_names
        
        if missing_cols or extra_cols:
            comparison["differences"].append({
                "field": "column_schema",
                "missing_columns": list(missing_cols),
                "extra_columns": list(extra_cols)
            })
        
        # Compare data types
        current_dtypes = current_metadata.get('dtypes', {})
        baseline_dtypes = baseline_metadata.get('dtypes', {})
        
        dtype_changes = []
        for col in current_col_names & baseline_col_names:
            if current_dtypes.get(col) != baseline_dtypes.get(col):
                dtype_changes.append({
                    "column": col,
                    "baseline_dtype": baseline_dtypes.get(col),
                    "current_dtype": current_dtypes.get(col)
                })
        
        if dtype_changes:
            comparison["differences"].append({
                "field": "data_types",
                "changes": dtype_changes
            })
        
        logger.info(f"Baseline comparison completed: {len(comparison['differences'])} difference(s) found")
        return comparison
    
    def save_metadata(self, metadata: Dict, file_id: str) -> Tuple[bool, str]:
        """
        Save standalone metadata file (for uploaded files, not baselines)
        
        Args:
            metadata: Metadata dictionary
            file_id: Unique file identifier
            
        Returns:
            Tuple of (success, message)
        """
        try:
            metadata_filename = f"{file_id}_metadata.json"
            metadata_path = self.baseline_path.parent / "raw" / metadata_filename
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Metadata saved: {metadata_path}")
            return True, f"Metadata saved for {file_id}"
            
        except Exception as e:
            error_msg = f"Error saving metadata: {str(e)}"
            log_error(error_msg, exception=e)
            return False, error_msg


# Convenience function to get VersioningManager instance
def get_versioning_manager() -> VersioningManager:
    """Get VersioningManager singleton instance"""
    return VersioningManager()