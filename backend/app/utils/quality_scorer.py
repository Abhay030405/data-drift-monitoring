"""
Quality Scorer for Neural Watch
Phase 2: Data Quality Checks
Calculate overall quality score and grade
"""
from typing import Dict
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from backend.app.utils.logger import NeuralWatchLogger

logger = NeuralWatchLogger.get_logger("quality_scorer")


class QualityScorer:
    """Calculate overall data quality score"""
    
    def __init__(self, missing_weight: float = 30.0, duplicate_weight: float = 25.0,
                 outlier_weight: float = 25.0, schema_weight: float = 20.0):
        """
        Initialize Quality Scorer
        
        Args:
            missing_weight: Weight for missing values (default: 30%)
            duplicate_weight: Weight for duplicates (default: 25%)
            outlier_weight: Weight for outliers (default: 25%)
            schema_weight: Weight for schema consistency (default: 20%)
        """
        self.missing_weight = missing_weight
        self.duplicate_weight = duplicate_weight
        self.outlier_weight = outlier_weight
        self.schema_weight = schema_weight
        
        # Validate weights sum to 100
        total = missing_weight + duplicate_weight + outlier_weight + schema_weight
        if abs(total - 100.0) > 0.01:
            logger.warning(f"Weights sum to {total}, normalizing to 100")
            self.missing_weight = (missing_weight / total) * 100
            self.duplicate_weight = (duplicate_weight / total) * 100
            self.outlier_weight = (outlier_weight / total) * 100
            self.schema_weight = (schema_weight / total) * 100
        
        logger.info(f"QualityScorer initialized | Weights: M:{self.missing_weight} D:{self.duplicate_weight} O:{self.outlier_weight} S:{self.schema_weight}")
    
    def calculate_score(self, missing_analysis: Dict, duplicate_analysis: Dict,
                       outlier_analysis: Dict, schema_analysis: Dict = None) -> Dict:
        """
        Calculate overall quality score
        
        Args:
            missing_analysis: Missing value analysis results
            duplicate_analysis: Duplicate analysis results
            outlier_analysis: Outlier analysis results
            schema_analysis: Schema consistency analysis (optional)
            
        Returns:
            Dictionary with score, grade, and breakdown
        """
        logger.info("Calculating overall quality score")
        
        # Missing values score (0-100, where 100 = no missing values)
        missing_pct = missing_analysis.get('overall_missing_percentage', 0)
        missing_score = max(0, 100 - missing_pct)
        
        # Duplicate score (0-100, where 100 = no duplicates)
        duplicate_pct = duplicate_analysis.get('duplicate_percentage', 0)
        duplicate_score = max(0, 100 - duplicate_pct)
        
        # Outlier score (0-100, where 100 = no outliers)
        outlier_pct = outlier_analysis.get('outlier_percentage', 0)
        outlier_score = max(0, 100 - min(outlier_pct, 100))
        
        # Schema consistency score (default 100 if not provided)
        if schema_analysis:
            schema_score = self._calculate_schema_score(schema_analysis)
        else:
            schema_score = 100.0
        
        # Calculate weighted overall score
        overall_score = (
            (missing_score * self.missing_weight / 100) +
            (duplicate_score * self.duplicate_weight / 100) +
            (outlier_score * self.outlier_weight / 100) +
            (schema_score * self.schema_weight / 100)
        )
        
        overall_score = round(overall_score, 2)
        
        # Determine grade
        grade = self._get_grade(overall_score)
        
        result = {
            "overall_score": overall_score,
            "grade": grade,
            "grade_emoji": self._get_grade_emoji(grade),
            "breakdown": {
                "missing_values": {
                    "score": round(missing_score, 2),
                    "weight": self.missing_weight,
                    "contribution": round(missing_score * self.missing_weight / 100, 2)
                },
                "duplicates": {
                    "score": round(duplicate_score, 2),
                    "weight": self.duplicate_weight,
                    "contribution": round(duplicate_score * self.duplicate_weight / 100, 2)
                },
                "outliers": {
                    "score": round(outlier_score, 2),
                    "weight": self.outlier_weight,
                    "contribution": round(outlier_score * self.outlier_weight / 100, 2)
                },
                "schema_consistency": {
                    "score": round(schema_score, 2),
                    "weight": self.schema_weight,
                    "contribution": round(schema_score * self.schema_weight / 100, 2)
                }
            }
        }
        
        logger.info(f"Quality score calculated: {overall_score}/100 ({grade})")
        return result
    
    def _calculate_schema_score(self, schema_analysis: Dict) -> float:
        """
        Calculate schema consistency score
        
        Args:
            schema_analysis: Schema analysis results
            
        Returns:
            Score from 0-100
        """
        # If all types are consistent, return 100
        if schema_analysis.get('all_valid', True):
            return 100.0
        
        # Otherwise, calculate based on inconsistencies
        inconsistencies = len(schema_analysis.get('inconsistencies', []))
        total_columns = schema_analysis.get('total_columns', 1)
        
        consistency_pct = ((total_columns - inconsistencies) / total_columns) * 100
        return max(0, consistency_pct)
    
    def _get_grade(self, score: float) -> str:
        """
        Convert score to letter grade
        
        Args:
            score: Quality score (0-100)
            
        Returns:
            Letter grade
        """
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 50:
            return "Poor"
        else:
            return "Critical"
    
    def _get_grade_emoji(self, grade: str) -> str:
        """
        Get emoji for grade
        
        Args:
            grade: Letter grade
            
        Returns:
            Emoji string
        """
        emoji_map = {
            "Excellent": "🟢",
            "Very Good": "🟢",
            "Good": "🟡",
            "Fair": "🟠",
            "Poor": "🔴",
            "Critical": "🔴"
        }
        return emoji_map.get(grade, "⚪")
    
    def get_recommendations(self, missing_analysis: Dict, duplicate_analysis: Dict,
                          outlier_analysis: Dict) -> list:
        """
        Generate prioritized recommendations
        
        Args:
            missing_analysis: Missing value analysis
            duplicate_analysis: Duplicate analysis
            outlier_analysis: Outlier analysis
            
        Returns:
            List of recommendations with priorities
        """
        recommendations = []
        
        # Missing values recommendations
        if missing_analysis.get('overall_missing_percentage', 0) > 0:
            for detail in missing_analysis.get('details', []):
                if detail['severity'] == 'high':
                    recommendations.append({
                        "priority": "high",
                        "category": "missing_values",
                        "message": f"Column '{detail['column']}' has {detail['missing_percentage']}% missing values",
                        "action": detail['recommendation']
                    })
                elif detail['severity'] == 'medium':
                    recommendations.append({
                        "priority": "medium",
                        "category": "missing_values",
                        "message": f"Column '{detail['column']}' has {detail['missing_percentage']}% missing values",
                        "action": detail['recommendation']
                    })
        
        # Duplicate recommendations
        if duplicate_analysis.get('duplicate_percentage', 0) > 0:
            severity = duplicate_analysis.get('severity', 'low')
            priority = "high" if severity == "high" else "medium" if severity == "medium" else "low"
            
            recommendations.append({
                "priority": priority,
                "category": "duplicates",
                "message": f"{duplicate_analysis['total_duplicates']} duplicate rows detected ({duplicate_analysis['duplicate_percentage']}%)",
                "action": duplicate_analysis['recommendation']
            })
        
        # Outlier recommendations
        if outlier_analysis.get('outlier_percentage', 0) > 0:
            for detail in outlier_analysis.get('details', []):
                if detail.get('outlier_count', 0) > 0:
                    severity = detail.get('severity', 'low')
                    priority = "high" if severity == "high" else "medium" if severity == "medium" else "low"
                    
                    recommendations.append({
                        "priority": priority,
                        "category": "outliers",
                        "message": f"Column '{detail['column']}' has {detail['outlier_count']} outliers ({detail['outlier_percentage']}%)",
                        "action": detail['recommendation']
                    })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return recommendations


# Convenience function
def calculate_quality_score(missing_analysis: Dict, duplicate_analysis: Dict,
                           outlier_analysis: Dict, schema_analysis: Dict = None) -> Dict:
    """
    Convenience function to calculate quality score
    
    Args:
        missing_analysis: Missing value analysis
        duplicate_analysis: Duplicate analysis
        outlier_analysis: Outlier analysis
        schema_analysis: Schema analysis (optional)
        
    Returns:
        Quality score results
    """
    scorer = QualityScorer()
    return scorer.calculate_score(missing_analysis, duplicate_analysis, outlier_analysis, schema_analysis)