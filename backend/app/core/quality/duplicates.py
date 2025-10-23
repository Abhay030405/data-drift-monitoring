"""
Duplicate Detector for Neural Watch
Phase 2: Data Quality Checks
Detects and analyzes duplicate rows in datasets
"""
import pandas as pd
from typing import Dict, List, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from backend.app.utils.logger import NeuralWatchLogger

logger = NeuralWatchLogger.get_logger("duplicates")


class DuplicateDetector:
    """Detect and analyze duplicate rows in datasets"""
    
    def __init__(self, check_full_row: bool = True, key_columns: Optional[List[str]] = None):
        """
        Initialize Duplicate Detector
        
        Args:
            check_full_row: Check for full row duplicates (default: True)
            key_columns: Specific columns to check for duplicates (optional)
        """
        self.check_full_row = check_full_row
        self.key_columns = key_columns
        logger.info(f"DuplicateDetector initialized | Full row: {check_full_row} | Keys: {key_columns}")
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Perform comprehensive duplicate analysis
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with duplicate analysis results
        """
        logger.info(f"Starting duplicate analysis for {len(df)} rows")
        
        total_rows = len(df)
        
        # Full row duplicate analysis
        if self.check_full_row:
            duplicates = df.duplicated(keep=False)
            duplicate_count = duplicates.sum()
            duplicate_percentage = round((duplicate_count / total_rows * 100), 2) if total_rows > 0 else 0
            
            # Count duplicate groups (unique duplicate combinations)
            if duplicate_count > 0:
                duplicate_groups = df[duplicates].drop_duplicates().shape[0]
            else:
                duplicate_groups = 0
            
            # Get sample duplicates
            sample_duplicates = self._get_sample_duplicates(df, limit=5)
            
        else:
            duplicate_count = 0
            duplicate_percentage = 0
            duplicate_groups = 0
            sample_duplicates = []
        
        # Key column duplicate analysis (if specified)
        key_analysis = None
        if self.key_columns and all(col in df.columns for col in self.key_columns):
            key_analysis = self._analyze_key_duplicates(df)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(duplicate_percentage)
        
        result = {
            "total_rows": total_rows,
            "total_duplicates": int(duplicate_count),
            "duplicate_percentage": duplicate_percentage,
            "duplicate_groups": duplicate_groups,
            "unique_rows": total_rows - int(duplicate_count),
            "check_full_row": self.check_full_row,
            "key_columns": self.key_columns,
            "key_analysis": key_analysis,
            "sample_duplicates": sample_duplicates,
            "recommendation": recommendation,
            "severity": self._get_severity(duplicate_percentage)
        }
        
        logger.info(f"Duplicate analysis complete: {duplicate_count} duplicates ({duplicate_percentage}%)")
        return result
    
    def _get_sample_duplicates(self, df: pd.DataFrame, limit: int = 5) -> List[Dict]:
        """
        Get sample duplicate row groups
        
        Args:
            df: DataFrame
            limit: Maximum number of groups to return
            
        Returns:
            List of sample duplicate groups
        """
        duplicates = df[df.duplicated(keep=False)]
        
        if duplicates.empty:
            return []
        
        samples = []
        seen_groups = 0
        
        # Group by all columns to find duplicate sets
        for _, group in duplicates.groupby(list(df.columns)):
            if seen_groups >= limit:
                break
            
            if len(group) > 1:
                samples.append({
                    "count": len(group),
                    "rows": group.head(3).to_dict('records')  # Show max 3 rows per group
                })
                seen_groups += 1
        
        return samples
    
    def _analyze_key_duplicates(self, df: pd.DataFrame) -> Dict:
        """
        Analyze duplicates based on key columns
        
        Args:
            df: DataFrame
            
        Returns:
            Key column duplicate analysis
        """
        key_duplicates = df.duplicated(subset=self.key_columns, keep=False)
        key_duplicate_count = key_duplicates.sum()
        key_duplicate_percentage = round((key_duplicate_count / len(df) * 100), 2)
        
        return {
            "columns": self.key_columns,
            "duplicate_count": int(key_duplicate_count),
            "duplicate_percentage": key_duplicate_percentage,
            "unique_combinations": df[self.key_columns].drop_duplicates().shape[0]
        }
    
    def _generate_recommendation(self, duplicate_percentage: float) -> str:
        """
        Generate recommendation for handling duplicates
        
        Args:
            duplicate_percentage: Percentage of duplicate rows
            
        Returns:
            Recommendation string
        """
        if duplicate_percentage == 0:
            return "no_action"
        elif duplicate_percentage < 1:
            return "keep_first"
        elif duplicate_percentage < 5:
            return "review_and_remove"
        elif duplicate_percentage < 20:
            return "investigate_cause"
        else:
            return "major_issue_investigate"
    
    def _get_severity(self, duplicate_percentage: float) -> str:
        """
        Determine severity level
        
        Args:
            duplicate_percentage: Percentage of duplicates
            
        Returns:
            Severity level
        """
        if duplicate_percentage == 0:
            return "none"
        elif duplicate_percentage < 1:
            return "low"
        elif duplicate_percentage < 5:
            return "medium"
        else:
            return "high"
    
    def get_duplicate_indices(self, df: pd.DataFrame, keep: str = 'first') -> List[int]:
        """
        Get indices of duplicate rows
        
        Args:
            df: DataFrame
            keep: Which duplicates to mark ('first', 'last', False for all)
            
        Returns:
            List of duplicate row indices
        """
        if self.check_full_row:
            duplicates = df.duplicated(keep=keep)
        elif self.key_columns:
            duplicates = df.duplicated(subset=self.key_columns, keep=keep)
        else:
            return []
        
        return df[duplicates].index.tolist()
    
    def remove_duplicates(self, df: pd.DataFrame, keep: str = 'first', inplace: bool = False) -> pd.DataFrame:
        """
        Remove duplicate rows
        
        Args:
            df: DataFrame
            keep: Which duplicates to keep ('first', 'last', False for none)
            inplace: Modify DataFrame in place
            
        Returns:
            DataFrame with duplicates removed
        """
        logger.info(f"Removing duplicates (keep={keep})")
        
        if self.check_full_row:
            result = df.drop_duplicates(keep=keep, inplace=inplace)
        elif self.key_columns:
            result = df.drop_duplicates(subset=self.key_columns, keep=keep, inplace=inplace)
        else:
            result = df
        
        if not inplace:
            removed = len(df) - len(result)
            logger.info(f"Removed {removed} duplicate rows")
            return result
        else:
            return df


# Convenience function
def detect_duplicates(df: pd.DataFrame, check_full_row: bool = True, 
                     key_columns: Optional[List[str]] = None) -> Dict:
    """
    Convenience function to detect duplicates
    
    Args:
        df: DataFrame to analyze
        check_full_row: Check for full row duplicates
        key_columns: Specific columns to check
        
    Returns:
        Duplicate analysis results
    """
    detector = DuplicateDetector(check_full_row, key_columns)
    return detector.analyze(df)