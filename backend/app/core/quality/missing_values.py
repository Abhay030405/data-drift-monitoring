"""
Missing Values Analyzer for Neural Watch
Phase 2: Data Quality Checks
Detects and analyzes missing values in datasets
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from backend.app.utils.logger import NeuralWatchLogger

logger = NeuralWatchLogger.get_logger("missing_values")


class MissingValueAnalyzer:
    """Analyze missing values in datasets"""
    
    def __init__(self, warn_threshold: float = 10.0, error_threshold: float = 50.0):
        """
        Initialize Missing Value Analyzer
        
        Args:
            warn_threshold: Percentage threshold for warning (default: 10%)
            error_threshold: Percentage threshold for error (default: 50%)
        """
        self.warn_threshold = warn_threshold
        self.error_threshold = error_threshold
        logger.info(f"MissingValueAnalyzer initialized | Warn: {warn_threshold}% | Error: {error_threshold}%")
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Perform comprehensive missing value analysis
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with missing value analysis results
        """
        logger.info(f"Starting missing value analysis for {len(df)} rows, {len(df.columns)} columns")
        
        # Calculate missing values per column
        missing_counts = df.isnull().sum()
        missing_percentages = (missing_counts / len(df) * 100).round(2)
        
        # Total missing values
        total_missing = int(missing_counts.sum())
        total_cells = len(df) * len(df.columns)
        overall_missing_percentage = round((total_missing / total_cells * 100), 2) if total_cells > 0 else 0
        
        # Columns with missing values
        columns_with_missing = missing_counts[missing_counts > 0].index.tolist()
        
        # Detailed analysis per column
        details = []
        for column in columns_with_missing:
            count = int(missing_counts[column])
            percentage = float(missing_percentages[column])
            
            # Determine severity
            if percentage >= self.error_threshold:
                severity = "high"
            elif percentage >= self.warn_threshold:
                severity = "medium"
            else:
                severity = "low"
            
            # Generate recommendation
            recommendation = self._generate_recommendation(df, column, percentage)
            
            details.append({
                "column": column,
                "missing_count": count,
                "missing_percentage": percentage,
                "severity": severity,
                "data_type": str(df[column].dtype),
                "recommendation": recommendation
            })
        
        # Sort by percentage (descending)
        details.sort(key=lambda x: x['missing_percentage'], reverse=True)
        
        result = {
            "total_missing": total_missing,
            "total_cells": total_cells,
            "overall_missing_percentage": overall_missing_percentage,
            "columns_affected": len(columns_with_missing),
            "columns_with_missing": columns_with_missing,
            "details": details,
            "summary": self._generate_summary(details)
        }
        
        logger.info(f"Missing value analysis complete: {total_missing} missing ({overall_missing_percentage}%)")
        return result
    
    def _generate_recommendation(self, df: pd.DataFrame, column: str, percentage: float) -> str:
        """
        Generate recommendation for handling missing values
        
        Args:
            df: DataFrame
            column: Column name
            percentage: Missing percentage
            
        Returns:
            Recommendation string
        """
        dtype = df[column].dtype
        
        # High missing percentage - consider dropping
        if percentage >= self.error_threshold:
            return "drop_column"
        
        # Numeric columns
        if pd.api.types.is_numeric_dtype(dtype):
            # Check skewness
            non_null_values = df[column].dropna()
            if len(non_null_values) > 0:
                skewness = non_null_values.skew()
                if abs(skewness) > 1:
                    return "impute_median"
                else:
                    return "impute_mean"
            return "impute_median"
        
        # Categorical columns
        elif pd.api.types.is_object_dtype(dtype) or pd.api.types.is_categorical_dtype(dtype):
            return "impute_mode"
        
        # Boolean columns
        elif pd.api.types.is_bool_dtype(dtype):
            return "impute_mode"
        
        # Datetime columns
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return "forward_fill"
        
        return "investigate"
    
    def _generate_summary(self, details: List[Dict]) -> Dict:
        """
        Generate summary statistics
        
        Args:
            details: List of column details
            
        Returns:
            Summary dictionary
        """
        if not details:
            return {
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0,
                "worst_column": None,
                "worst_percentage": 0
            }
        
        high_count = sum(1 for d in details if d['severity'] == 'high')
        medium_count = sum(1 for d in details if d['severity'] == 'medium')
        low_count = sum(1 for d in details if d['severity'] == 'low')
        
        worst = details[0]  # Already sorted by percentage
        
        return {
            "high_severity": high_count,
            "medium_severity": medium_count,
            "low_severity": low_count,
            "worst_column": worst['column'],
            "worst_percentage": worst['missing_percentage']
        }
    
    def get_missing_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Identify missing value patterns (rows with multiple missing values)
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with pattern analysis
        """
        # Count missing values per row
        missing_per_row = df.isnull().sum(axis=1)
        
        # Rows with at least one missing value
        rows_with_missing = (missing_per_row > 0).sum()
        rows_with_missing_pct = round((rows_with_missing / len(df) * 100), 2)
        
        # Rows with multiple missing values
        rows_with_multiple = (missing_per_row > 1).sum()
        
        # Completely empty rows
        completely_empty = (missing_per_row == len(df.columns)).sum()
        
        return {
            "rows_with_missing": int(rows_with_missing),
            "rows_with_missing_percentage": rows_with_missing_pct,
            "rows_with_multiple_missing": int(rows_with_multiple),
            "completely_empty_rows": int(completely_empty),
            "max_missing_per_row": int(missing_per_row.max()),
            "avg_missing_per_row": round(missing_per_row.mean(), 2)
        }
    
    def visualize_heatmap_data(self, df: pd.DataFrame, sample_size: int = 100) -> Dict:
        """
        Prepare data for missing value heatmap visualization
        
        Args:
            df: DataFrame to analyze
            sample_size: Number of rows to include in heatmap
            
        Returns:
            Dictionary with heatmap data
        """
        # Sample data if too large
        if len(df) > sample_size:
            df_sample = df.sample(n=sample_size, random_state=42)
        else:
            df_sample = df
        
        # Create binary missing matrix (1 = missing, 0 = present)
        missing_matrix = df_sample.isnull().astype(int)
        
        return {
            "rows": len(df_sample),
            "columns": df_sample.columns.tolist(),
            "matrix": missing_matrix.values.tolist(),
            "row_indices": df_sample.index.tolist()
        }


# Convenience function
def analyze_missing_values(df: pd.DataFrame, warn_threshold: float = 10.0, 
                          error_threshold: float = 50.0) -> Dict:
    """
    Convenience function to analyze missing values
    
    Args:
        df: DataFrame to analyze
        warn_threshold: Warning threshold percentage
        error_threshold: Error threshold percentage
        
    Returns:
        Missing value analysis results
    """
    analyzer = MissingValueAnalyzer(warn_threshold, error_threshold)
    return analyzer.analyze(df)