"""
Data Upload API Routes for Neural Watch
Phase 1: Data Ingestion & Quality Setup
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List
from pathlib import Path
import shutil
import time
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent.parent))
from backend.app.api.dependencies import get_file_handler, get_versioning_manager, get_logger
from backend.app.utils.file_handler import FileHandler
from backend.app.utils.versioning import VersioningManager
from backend.app.utils.logger import log_upload, log_api_request
from config.settings import DATA_RAW_PATH

router = APIRouter(prefix="/api/v1", tags=["data_upload"])


@router.post("/upload_data")
async def upload_data(
    file: UploadFile = File(...),
    is_baseline: Optional[bool] = Form(False),
    description: Optional[str] = Form(None),
    file_handler: FileHandler = Depends(get_file_handler),
    versioning_manager: VersioningManager = Depends(get_versioning_manager)
):
    """
    Upload a dataset file (CSV/JSON/Parquet)
    
    Args:
        file: Uploaded file
        is_baseline: Whether to set this as a baseline version
        description: Optional description for the dataset
        
    Returns:
        JSON response with upload status and metadata
    """
    start_time = time.time()
    
    try:
        # Step 1: Validate file format
        is_valid_format, format_message = file_handler.validate_file_format(file.filename)
        if not is_valid_format:
            log_upload(file.filename, "rejected", {"reason": format_message})
            raise HTTPException(status_code=400, detail=format_message)
        
        # Step 2: Save uploaded file temporarily
        temp_path = DATA_RAW_PATH / f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Step 3: Validate file size
        is_valid_size, size_message = file_handler.validate_file_size(temp_path)
        if not is_valid_size:
            temp_path.unlink()  # Delete temp file
            log_upload(file.filename, "rejected", {"reason": size_message})
            raise HTTPException(status_code=400, detail=size_message)
        
        # Step 4: Read file into DataFrame
        df, read_error = file_handler.read_file(temp_path)
        if df is None:
            temp_path.unlink()
            log_upload(file.filename, "failed", {"reason": read_error})
            raise HTTPException(status_code=400, detail=f"Error reading file: {read_error}")
        
        # Step 5: Check for duplicate files
        file_hash = file_handler.compute_file_hash(temp_path)
        is_duplicate, existing_file = file_handler.check_duplicate_file(file_hash)
        
        # Exclude the temp file itself from duplicate check
        if is_duplicate and existing_file != str(temp_path):
            temp_path.unlink()
            log_upload(file.filename, "rejected", {"reason": "duplicate", "existing": existing_file})
            raise HTTPException(
                status_code=409, 
                detail=f"Duplicate file detected. Existing file: {existing_file}"
            )
        
        
        # Step 6: Validate DataFrame against baseline (if exists)
        latest_baseline = versioning_manager.get_latest_baseline()
        validation_report = None
        
        if latest_baseline and not is_baseline:
            baseline_metadata = latest_baseline['source_metadata']
            expected_columns = baseline_metadata.get('column_names')
            expected_dtypes = baseline_metadata.get('dtypes')
            
            is_valid, validation_message, validation_report = file_handler.validate_dataframe(
                df, file.filename, expected_columns, expected_dtypes
            )
            
            if not is_valid:
                temp_path.unlink()
                log_upload(file.filename, "rejected", {"reason": validation_message})
                raise HTTPException(status_code=400, detail=f"Validation failed: {validation_message}")
        else:
            # Basic validation without baseline
            is_valid, validation_message, validation_report = file_handler.validate_dataframe(
                df, file.filename
            )
            if not is_valid:
                temp_path.unlink()
                log_upload(file.filename, "rejected", {"reason": validation_message})
                raise HTTPException(status_code=400, detail=f"Validation failed: {validation_message}")
        
        # Step 7: Compute metadata
        metadata = file_handler.compute_metadata(df, file.filename, temp_path)
        metadata['description'] = description
        metadata['is_baseline'] = is_baseline
        
        # Step 8: Save file to raw directory
        success, save_message, saved_path = file_handler.save_file(
            df, DATA_RAW_PATH, file.filename
        )
        
        if not success:
            temp_path.unlink()
            log_upload(file.filename, "failed", {"reason": save_message})
            raise HTTPException(status_code=500, detail=f"Error saving file: {save_message}")
        
        # Step 9: Create baseline if requested or if no baseline exists
        baseline_info = None
        if is_baseline or latest_baseline is None:
            success, baseline_message, baseline_info = versioning_manager.create_baseline_version(
                saved_path, metadata, description
            )
            
            if not success:
                log_upload(file.filename, "partial", {"reason": "baseline creation failed"})
            else:
                metadata['baseline_version'] = baseline_info['version_id']
        
        # Step 10: Compare with baseline
        comparison = None
        if latest_baseline and not is_baseline:
            comparison = versioning_manager.compare_with_baseline(
                metadata, latest_baseline['version_id']
            )
        
        # Step 11: Clean up temp file
        if temp_path.exists():
            temp_path.unlink()
        
        # Step 12: Prepare response
        response_time = time.time() - start_time
        
        response_data = {
            "status": "success",
            "message": "File uploaded successfully",
            "file_id": saved_path.stem,
            "filename": file.filename,
            "saved_as": saved_path.name,
            "upload_timestamp": datetime.now().isoformat(),
            "response_time_seconds": round(response_time, 3),
            "metadata": {
                "rows": metadata['rows'],
                "columns": metadata['columns'],
                "file_size_mb": metadata['file_size_mb'],
                "column_names": metadata['column_names'],
                "missing_values": metadata['missing_values'],
                "duplicates": metadata['duplicates']
            },
            "validation_report": validation_report,
            "baseline_info": baseline_info if baseline_info else None,
            "comparison_with_baseline": comparison
        }
        
        log_upload(file.filename, "success", {
            "file_id": saved_path.stem,
            "rows": metadata['rows'],
            "columns": metadata['columns']
        })
        
        log_api_request("/upload_data", "POST", 200, response_time)
        
        return JSONResponse(content=response_data, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on unexpected error
        if temp_path.exists():
            temp_path.unlink()
        
        log_upload(file.filename, "error", {"exception": str(e)})
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/list_uploads")
async def list_uploads(
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    List all uploaded files
    
    Returns:
        JSON response with list of uploaded files and their metadata
    """
    start_time = time.time()
    
    try:
        uploaded_files = []
        
        # Scan raw data directory
        for file_path in DATA_RAW_PATH.glob('*'):
            if file_path.is_file() and not file_path.name.startswith('temp_'):
                try:
                    # Read basic metadata
                    file_stat = file_path.stat()
                    
                    uploaded_files.append({
                        "file_id": file_path.stem,
                        "filename": file_path.name,
                        "file_size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                        "upload_timestamp": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        "file_path": str(file_path)
                    })
                except Exception as e:
                    continue
        
        # Sort by upload timestamp (newest first)
        uploaded_files.sort(key=lambda x: x['upload_timestamp'], reverse=True)
        
        response_time = time.time() - start_time
        log_api_request("/list_uploads", "GET", 200, response_time)
        
        return JSONResponse(content={
            "status": "success",
            "count": len(uploaded_files),
            "files": uploaded_files
        }, status_code=200)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing uploads: {str(e)}")


@router.get("/get_file_metadata/{file_id}")
async def get_file_metadata(
    file_id: str,
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Get detailed metadata for a specific uploaded file
    
    Args:
        file_id: File identifier (stem of filename)
        
    Returns:
        JSON response with detailed metadata
    """
    start_time = time.time()
    
    try:
        # Find file by ID
        file_path = None
        for f in DATA_RAW_PATH.glob(f"{file_id}*"):
            if f.is_file():
                file_path = f
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found")
        
        # Read file and compute metadata
        df, read_error = file_handler.read_file(file_path)
        if df is None:
            raise HTTPException(status_code=500, detail=f"Error reading file: {read_error}")
        
        metadata = file_handler.compute_metadata(df, file_path.name, file_path)
        
        response_time = time.time() - start_time
        log_api_request(f"/get_file_metadata/{file_id}", "GET", 200, response_time)
        
        return JSONResponse(content={
            "status": "success",
            "file_id": file_id,
            "metadata": metadata
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metadata: {str(e)}")


@router.delete("/delete_upload/{file_id}")
async def delete_upload(
    file_id: str,
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Delete an uploaded file (does NOT delete baselines)
    
    Args:
        file_id: File identifier to delete
        
    Returns:
        JSON response with deletion status
    """
    start_time = time.time()
    
    try:
        # Find file by ID
        file_path = None
        for f in DATA_RAW_PATH.glob(f"{file_id}*"):
            if f.is_file():
                file_path = f
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found")
        
        # Delete file
        file_path.unlink()
        
        response_time = time.time() - start_time
        log_api_request(f"/delete_upload/{file_id}", "DELETE", 200, response_time)
        
        return JSONResponse(content={
            "status": "success",
            "message": f"File '{file_id}' deleted successfully"
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@router.get("/list_baselines")
async def list_baselines(
    versioning_manager: VersioningManager = Depends(get_versioning_manager)
):
    """
    List all baseline versions
    
    Returns:
        JSON response with list of baselines
    """
    start_time = time.time()
    
    try:
        baselines = versioning_manager.list_baseline_versions()
        
        response_time = time.time() - start_time
        log_api_request("/list_baselines", "GET", 200, response_time)
        
        return JSONResponse(content={
            "status": "success",
            "count": len(baselines),
            "baselines": baselines
        }, status_code=200)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing baselines: {str(e)}")


@router.get("/get_baseline/{version_id}")
async def get_baseline(
    version_id: str,
    versioning_manager: VersioningManager = Depends(get_versioning_manager)
):
    """
    Get baseline information for a specific version
    
    Args:
        version_id: Baseline version identifier
        
    Returns:
        JSON response with baseline details
    """
    start_time = time.time()
    
    try:
        baseline_info = versioning_manager.get_baseline_by_version(version_id)
        
        if not baseline_info:
            raise HTTPException(status_code=404, detail=f"Baseline '{version_id}' not found")
        
        response_time = time.time() - start_time
        log_api_request(f"/get_baseline/{version_id}", "GET", 200, response_time)
        
        return JSONResponse(content={
            "status": "success",
            "baseline": baseline_info
        }, status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving baseline: {str(e)}")