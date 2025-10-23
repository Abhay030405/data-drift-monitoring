"""
Outlier Detector for Neural Watch
Phase 2: Data Quality Checks
Detects outliers using IQR, Z-Score, and Isolation Forest methods
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from backend.app.utils.logger import NeuralWatchLogger

logger = NeuralWatchLogger.get_logger("outliers")


class OutlierDetector:
    """Detect outliers in numerical columns using multiple methods"""
    
    def __init__(self, method: str = 'iqr', iqr_multiplier: float = 1.5, 
                 z_score_threshold: float = 3.0, use_isolation_forest: bool = False):
        """
        Initialize Outlier Detector
        
        Args:
            method: Detection method ('iqr', 'z_score', 'both')
            iqr_multiplier: IQR multiplier (default: 1.5)
            z_score_threshold: Z-score threshold (default: 3.0)
            use_isolation_forest: Use Isolation Forest for multivariate detection
        """
        self.method = method
        self.iqr_multiplier = iqr_multiplier
        self.z_score_threshold = z_score_threshold
        self.use_isolation_forest = use_isolation_forest
        
        logger.info(f"OutlierDetector initialized | Method: {method} | IQR: {iqr_multiplier} | Z: {z_score_threshold}")
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Perform comprehensive outlier analysis
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with outlier analysis results
        """
        logger.info(f"Starting outlier analysis for {len(df)} rows")
        
        # Get numerical columns only
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_columns:
            logger.warning("No numerical columns found for outlier detection")
            return {
                "total_outliers": 0,
                "outlier_percentage": 0,
                "columns_with_outliers": [],
                "details": [],
                "method": self.method
            }
        
        logger.info(f"Analyzing {len(numeric_columns)} numerical columns")
        
        details = []
        total_outliers = 0
        
        for column in numeric_columns:
            column_analysis = self._analyze_column(df, column)
            if column_analysis:
                details.append(column_analysis)
                total_outliers += column_analysis['outlier_count']
        
        # Calculate overall statistics
        total_values = len(df) * len(numeric_columns)
        outlier_percentage = round((total_outliers / total_values * 100), 2) if total_values > 0 else 0
        
        columns_with_outliers = [d['column'] for d in details if d['outlier_count'] > 0]
        
        result = {
            "total_outliers": total_outliers,
            "total_numeric_values": total_values,
            "outlier_percentage": outlier_percentage,
            "columns_analyzed": len(numeric_columns),
            "columns_with_outliers": columns_with_outliers,
            "details": details,
            "method": self.method
        }
        
        # Multivariate outlier detection (optional)
        if self.use_isolation_forest and len(numeric_columns) > 1:
            result['multivariate'] = self._isolation_forest_detection(df[numeric_columns])
        
        logger.info(f"Outlier analysis complete: {total_outliers} outliers ({outlier_percentage}%)")
        return result
    
    def _analyze_column(self, df: pd.DataFrame, column: str) -> Optional[Dict]:
        """
        Analyze outliers in a single column
        
        Args:
            df: DataFrame
            column: Column name
            
        Returns:
            Column outlier analysis or None if no data
        """
        data = df[column].dropna()
        
        if len(data) == 0:
            return None
        
        # IQR Method
        iqr_outliers = None
        if self.method in ['iqr', 'both']:
            iqr_outliers = self._detect_iqr_outliers(data)
        
        # Z-Score Method
        zscore_outliers = None
        if self.method in ['z_score', 'both']:
            zscore_outliers = self._detect_zscore_outliers(data)
        
        # Combine results based on method
        if self.method == 'both':
            # Union of both methods
            outlier_mask = iqr_outliers['mask'] | zscore_outliers['mask']
            outlier_count = outlier_mask.sum()
            outlier_values = data[outlier_mask].tolist()
            lower_bound = iqr_outliers['lower_bound']
            upper_bound = iqr_outliers['upper_bound']
        elif self.method == 'iqr':
            outlier_mask = iqr_outliers['mask']
            outlier_count = iqr_outliers['count']
            outlier_values = iqr_outliers['values']
            lower_bound = iqr_outliers['lower_bound']
            upper_bound = iqr_outliers['upper_bound']
        else:  # z_score
            outlier_mask = zscore_outliers['mask']
            outlier_count = zscore_outliers['count']
            outlier_values = zscore_outliers['values']
            lower_bound = None
            upper_bound = None
        
        outlier_percentage = round((outlier_count / len(data) * 100), 2)
        
        # Sample outliers (max 10)
        sample_outliers = sorted(outlier_values)[:5] + sorted(outlier_values, reverse=True)[:5]
        sample_outliers = list(set(sample_outliers))[:10]
        
        # Statistics
        stats = {
            'mean': float(data.mean()),
            'median': float(data.median()),
            'std': float(data.std()),
            'min': float(data.min()),
            'max': float(data.max()),
            'q1': float(data.quantile(0.25)),
            'q3': float(data.quantile(0.75))
        }
        
        # Generate recommendation
        recommendation = self._generate_recommendation(outlier_percentage, data)
        
        return {
            "column": column,
            "method": self.method,
            "outlier_count": int(outlier_count),
            "total_values": len(data),
            "outlier_percentage": outlier_percentage,
            "lower_bound": float(lower_bound) if lower_bound is not None else None,
            "upper_bound": float(upper_bound) if upper_bound is not None else None,
            "sample_outliers": [float(x) for x in sample_outliers],
            "statistics": stats,
            "recommendation": recommendation,
            "severity": self._get_severity(outlier_percentage)
        }
    
    def _detect_iqr_outliers(self, data: pd.Series) -> Dict:
        """
        Detect outliers using IQR method
        
        Args:
            data: Series of numerical data
            
        Returns:
            Dictionary with IQR outlier results
        """
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - self.iqr_multiplier * IQR
        upper_bound = Q3 + self.iqr_multiplier * IQR
        
        outlier_mask = (data < lower_bound) | (data > upper_bound)
        outliers = data[outlier_mask]
        
        return {
            'mask': outlier_mask,
            'count': len(outliers),
            'values': outliers.tolist(),
            'lower_bound': lower_bound,
            'upper_bound': upper_bound
        }
    
    def _detect_zscore_outliers(self, data: pd.Series) -> Dict:
        """
        Detect outliers using Z-Score method
        
        Args:
            data: Series of numerical data
            
        Returns:
            Dictionary with Z-score outlier results
        """
        mean = data.mean()
        std = data.std()
        
        if std == 0:
            return {
                'mask': pd.Series([False] * len(data), index=data.index),
                'count': 0,
                'values': []
            }
        
        z_scores = np.abs((data - mean) / std)
        outlier_mask = z_scores > self.z_score_threshold
        outliers = data[outlier_mask]
        
        return {
            'mask': outlier_mask,
            'count': len(outliers),
            'values': outliers.tolist()
        }
    
    def _isolation_forest_detection(self, df_numeric: pd.DataFrame) -> Dict:
        """
        Detect multivariate outliers using Isolation Forest
        
        Args:
            df_numeric: DataFrame with only numerical columns
            
        Returns:
            Isolation Forest results
        """
        try:
            from sklearn.ensemble import IsolationForest
            
            # Remove rows with any NaN
            df_clean = df_numeric.dropna()
            
            if len(df_clean) < 10:
                return {"error": "Insufficient data for Isolation Forest"}
            
            # Fit Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            predictions = iso_forest.fit_predict(df_clean)
            
            # -1 indicates outlier, 1 indicates inlier
            outlier_count = (predictions == -1).sum()
            outlier_percentage = round((outlier_count / len(df_clean) * 100), 2)
            
            return {
                "method": "isolation_forest",
                "outlier_count": int(outlier_count),
                "total_rows": len(df_clean),
                "outlier_percentage": outlier_percentage,
                "outlier_indices": df_clean[predictions == -1].index.tolist()[:10]  # Sample
            }
            
        except ImportError:
            logger.warning("scikit-learn not installed, skipping Isolation Forest")
            return {"error": "scikit-learn not installed"}
        except Exception as e:
            logger.error(f"Isolation Forest error: {str(e)}")
            return {"error": str(e)}
    
    def _generate_recommendation(self, outlier_percentage: float, data: pd.Series) -> str:
        """
        Generate recommendation for handling outliers
        
        Args:
            outlier_percentage: Percentage of outliers
            data: Original data series
            
        Returns:
            Recommendation string
        """
        if outlier_percentage == 0:
            return "no_action"
        elif outlier_percentage < 1:
            return "investigate"
        elif outlier_percentage < 5:
            # Check if data is highly skewed
            if abs(data.skew()) > 1:
                return "transform_log"
            else:
                return "winsorize"
        elif outlier_percentage < 10:
            return "clip_bounds"
        else:
            return "investigate_data_quality"
    
    def _get_severity(self, outlier_percentage: float) -> str:
        """
        Determine severity level
        
        Args:
            outlier_percentage: Percentage of outliers
            
        Returns:
            Severity level
        """
        if outlier_percentage == 0:
            return "none"
        elif outlier_percentage < 1:
            return "low"
        elif outlier_percentage < 5:
            return "medium"
        else:
            return "high"
    
    def get_outlier_bounds(self, df: pd.DataFrame, column: str) -> Tuple[float, float]:
        """
        Get outlier bounds for a specific column
        
        Args:
            df: DataFrame
            column: Column name
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        data = df[column].dropna()
        
        if self.method == 'iqr' or self.method == 'both':
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - self.iqr_multiplier * IQR
            upper_bound = Q3 + self.iqr_multiplier * IQR
            
            return float(lower_bound), float(upper_bound)
        else:
            # For z-score, use mean ± threshold * std
            mean = data.mean()
            std = data.std()
            
            lower_bound = mean - self.z_score_threshold * std
            upper_bound = mean + self.z_score_threshold * std
            
            return float(lower_bound), float(upper_bound)
    
    def remove_outliers(self, df: pd.DataFrame, column: str, inplace: bool = False) -> pd.DataFrame:
        """
        Remove outlier rows for a specific column
        
        Args:
            df: DataFrame
            column: Column name
            inplace: Modify DataFrame in place
            
        Returns:
            DataFrame with outliers removed
        """
        lower_bound, upper_bound = self.get_outlier_bounds(df, column)
        
        if inplace:
            df.drop(df[(df[column] < lower_bound) | (df[column] > upper_bound)].index, inplace=True)
            return df
        else:
            return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
    
    def clip_outliers(self, df: pd.DataFrame, column: str, inplace: bool = False) -> pd.DataFrame:
        """
        Clip outliers to bounds (winsorization)
        
        Args:
            df: DataFrame
            column: Column name
            inplace: Modify DataFrame in place
            
        Returns:
            DataFrame with outliers clipped
        """
        lower_bound, upper_bound = self.get_outlier_bounds(df, column)
        
        if inplace:
            df[column] = df[column].clip(lower=lower_bound, upper=upper_bound)
            return df
        else:
            result = df.copy()
            result[column] = result[column].clip(lower=lower_bound, upper=upper_bound)
            return result


# Convenience function
def detect_outliers(df: pd.DataFrame, method: str = 'iqr', 
                   iqr_multiplier: float = 1.5, z_score_threshold: float = 3.0,
                   use_isolation_forest: bool = False) -> Dict:
    """
    Convenience function to detect outliers
    
    Args:
        df: DataFrame to analyze
        method: Detection method ('iqr', 'z_score', 'both')
        iqr_multiplier: IQR multiplier
        z_score_threshold: Z-score threshold
        use_isolation_forest: Use Isolation Forest
        
    Returns:
        Outlier analysis results
    """
    detector = OutlierDetector(method, iqr_multiplier, z_score_threshold, use_isolation_forest)
    return detector.analyze(df)