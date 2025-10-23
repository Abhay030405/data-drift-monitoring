"""
Quality Check API Routes for Neural Watch
Phase 2: Data Quality Checks
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
from pathlib import Path
import time
from datetime import datetime
import json

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent.parent))
from backend.app.api.dependencies import get_file_handler, get_logger
from backend.app.utils.file_handler import FileHandler
from backend.app.core.quality import MissingValueAnalyzer, DuplicateDetector, OutlierDetector
from backend.app.utils.quality_scorer import QualityScorer
from backend.app.utils.logger import log_api_request
from config.settings import DATA_RAW_PATH, DRIFT_REPORTS_PATH

router = APIRouter(prefix="/api/v1", tags=["quality_check"])


@router.post("/check_quality")
async def check_quality(
    file_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    check_missing: bool = Form(True),
    check_duplicates: bool = Form(True),
    check_outliers: bool = Form(True),
    outlier_method: str = Form('iqr'),
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Run comprehensive quality checks on a dataset
    
    Args:
        file_id: ID of previously uploaded file (optional)
        file: New file to upload and check (optional)
        check_missing: Run missing value analysis
        check_duplicates: Run duplicate detection
        check_outliers: Run outlier detection
        outlier_method: Outlier detection method ('iqr', 'z_score', 'both')
        
    Returns:
        JSON response with comprehensive quality report
    """
    start_time = time.time()
    
    try:
        # Determine data source
        if file_id:
            # Load existing file
            file_path = None
            for f in DATA_RAW_PATH.glob(f"{file_id}*"):
                if f.is_file():
                    file_path = f
                    break
            
            if not file_path:
                raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found")
            
            df, read_error = file_handler.read_file(file_path)
            if df is None:
                raise HTTPException(status_code=500, detail=f"Error reading file: {read_error}")
            
            filename = file_path.name
        
        elif file:
            # Handle uploaded file
            import shutil
            temp_path = DATA_RAW_PATH / f"temp_quality_{file.filename}"
            
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            df, read_error = file_handler.read_file(temp_path)
            if df is None:
                temp_path.unlink()
                raise HTTPException(status_code=400, detail=f"Error reading file: {read_error}")
            
            filename = file.filename
            file_id = f"temp_{int(time.time())}"
            
            # Clean up temp file after reading
            temp_path.unlink()
        
        else:
            raise HTTPException(status_code=400, detail="Either file_id or file must be provided")
        
        # Generate report ID
        report_id = f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize report
        quality_report = {
            "report_id": report_id,
            "file_id": file_id,
            "filename": filename,
            "timestamp": datetime.now().isoformat(),
            "dataset_info": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
        }
        
        # Run quality checks
        
        # 1. Missing Values Analysis
        if check_missing:
            analyzer = MissingValueAnalyzer(warn_threshold=10.0, error_threshold=50.0)
            missing_analysis = analyzer.analyze(df)
            missing_patterns = analyzer.get_missing_patterns(df)
            
            quality_report['missing_values'] = missing_analysis
            quality_report['missing_patterns'] = missing_patterns
        else:
            quality_report['missing_values'] = {"total_missing": 0, "overall_missing_percentage": 0, "details": []}
        
        # 2. Duplicate Detection
        if check_duplicates:
            detector = DuplicateDetector(check_full_row=True)
            duplicate_analysis = detector.analyze(df)
            
            quality_report['duplicates'] = duplicate_analysis
        else:
            quality_report['duplicates'] = {"total_duplicates": 0, "duplicate_percentage": 0}
        
        # 3. Outlier Detection
        if check_outliers:
            outlier_detector = OutlierDetector(method=outlier_method, iqr_multiplier=1.5, z_score_threshold=3.0)
            outlier_analysis = outlier_detector.analyze(df)
            
            quality_report['outliers'] = outlier_analysis
        else:
            quality_report['outliers'] = {"total_outliers": 0, "outlier_percentage": 0, "details": []}
        
        # 4. Calculate Overall Quality Score
        scorer = QualityScorer()
        score_result = scorer.calculate_score(
            quality_report['missing_values'],
            quality_report['duplicates'],
            quality_report['outliers']
        )
        
        quality_report['quality_score'] = score_result
        
        # 5. Generate Recommendations
        recommendations = scorer.get_recommendations(
            quality_report['missing_values'],
            quality_report['duplicates'],
            quality_report['outliers']
        )
        
        quality_report['recommendations'] = recommendations
        
        # 6. Summary Statistics
        quality_report['summary'] = {
            "total_issues": (
                len(quality_report['missing_values'].get('details', [])) +
                (1 if quality_report['duplicates']['total_duplicates'] > 0 else 0) +
                len([d for d in quality_report['outliers'].get('details', []) if d['outlier_count'] > 0])
            ),
            "high_priority_issues": len([r for r in recommendations if r['priority'] == 'high']),
            "medium_priority_issues": len([r for r in recommendations if r['priority'] == 'medium']),
            "low_priority_issues": len([r for r in recommendations if r['priority'] == 'low'])
        }
        
        # 7. Save report to file
        report_path = DRIFT_REPORTS_PATH / f"{report_id}.json"
        with open(report_path, 'w') as f:
            json.dump(quality_report, f, indent=2)
        
        # Calculate response time
        response_time = time.time() - start_time
        quality_report['response_time_seconds'] = round(response_time, 3)
        
        log_api_request("/check_quality", "POST", 200, response_time)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Quality check completed",
            "report": quality_report
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quality check error: {str(e)}")


@router.get("/quality_report/{report_id}")
async def get_quality_report(report_id: str):
    """
    Retrieve a saved quality report
    
    Args:
        report_id: Report identifier
        
    Returns:
        JSON response with quality report
    """
    start_time = time.time()
    
    try:
        report_path = DRIFT_REPORTS_PATH / f"{report_id}.json"
        
        if not report_path.exists():
            raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        response_time = time.time() - start_time
        log_api_request(f"/quality_report/{report_id}", "GET", 200, response_time)
        
        return JSONResponse(content={
            "status": "success",
            "report": report
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")


@router.get("/quality_summary/{file_id}")
async def get_quality_summary(
    file_id: str,
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Get quick quality summary for a file (without full analysis)
    
    Args:
        file_id: File identifier
        
    Returns:
        JSON response with quick quality summary
    """
    start_time = time.time()
    
    try:
        # Find file
        file_path = None
        for f in DATA_RAW_PATH.glob(f"{file_id}*"):
            if f.is_file():
                file_path = f
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found")
        
        # Read file
        df, read_error = file_handler.read_file(file_path)
        if df is None:
            raise HTTPException(status_code=500, detail=f"Error reading file: {read_error}")
        
        # Quick analysis
        missing_count = df.isnull().sum().sum()
        missing_pct = round((missing_count / (len(df) * len(df.columns)) * 100), 2)
        
        duplicate_count = df.duplicated().sum()
        duplicate_pct = round((duplicate_count / len(df) * 100), 2)
        
        summary = {
            "file_id": file_id,
            "filename": file_path.name,
            "rows": len(df),
            "columns": len(df.columns),
            "missing_values": {
                "count": int(missing_count),
                "percentage": missing_pct
            },
            "duplicates": {
                "count": int(duplicate_count),
                "percentage": duplicate_pct
            },
            "quick_score": round(100 - (missing_pct * 0.3 + duplicate_pct * 0.7), 2)
        }
        
        response_time = time.time() - start_time
        log_api_request(f"/quality_summary/{file_id}", "GET", 200, response_time)
        
        return JSONResponse(content={
            "status": "success",
            "summary": summary
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")


@router.get("/list_quality_reports")
async def list_quality_reports():
    """
    List all saved quality reports
    
    Returns:
        JSON response with list of reports
    """
    start_time = time.time()
    
    try:
        reports = []
        
        for report_file in DRIFT_REPORTS_PATH.glob("quality_report_*.json"):
            try:
                with open(report_file, 'r') as f:
                    report = json.load(f)
                
                reports.append({
                    "report_id": report['report_id'],
                    "filename": report['filename'],
                    "timestamp": report['timestamp'],
                    "quality_score": report.get('quality_score', {}).get('overall_score', 0),
                    "grade": report.get('quality_score', {}).get('grade', 'Unknown')
                })
            except Exception:
                continue
        
        # Sort by timestamp (newest first)
        reports.sort(key=lambda x: x['timestamp'], reverse=True)
        
        response_time = time.time() - start_time
        log_api_request("/list_quality_reports", "GET", 200, response_time)
        
        return JSONResponse(content={
            "status": "success",
            "count": len(reports),
            "reports": reports
        }, status_code=200)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing reports: {str(e)}")