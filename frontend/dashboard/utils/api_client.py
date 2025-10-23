"""
API Client for Neural Watch Frontend
Phase 1 & 2: Data Ingestion & Quality Checks
Handles communication with backend APIs
"""
import requests
from typing import Dict, Optional, Tuple, List
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from config.settings import BACKEND_URL


class APIClient:
    """Client for communicating with Neural Watch backend API"""
    
    def __init__(self, base_url: str = BACKEND_URL):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of the backend API
        """
        self.base_url = base_url
        self.timeout = 300  # 5 minutes for large file uploads
    
    def _handle_response(self, response: requests.Response) -> Tuple[bool, Dict]:
        """
        Handle API response and extract data
        
        Args:
            response: requests Response object
            
        Returns:
            Tuple of (success, response_data)
        """
        try:
            response.raise_for_status()
            return True, response.json()
        except requests.exceptions.HTTPError as e:
            error_data = response.json() if response.content else {"detail": str(e)}
            return False, error_data
        except Exception as e:
            return False, {"detail": f"Error: {str(e)}"}
    
    def health_check(self) -> Tuple[bool, Dict]:
        """
        Check backend health status
        
        Returns:
            Tuple of (success, health_data)
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return self._handle_response(response)
        except Exception as e:
            return False, {"detail": f"Cannot connect to backend: {str(e)}"}
    
    def upload_file(
        self, 
        file_path: Path, 
        is_baseline: bool = False,
        description: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        Upload a dataset file to the backend
        
        Args:
            file_path: Path to the file to upload
            is_baseline: Whether to set as baseline
            description: Optional description
            
        Returns:
            Tuple of (success, response_data)
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f)}
                data = {
                    'is_baseline': str(is_baseline).lower(),
                    'description': description or ''
                }
                
                response = requests.post(
                    f"{self.base_url}/api/v1/upload_data",
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
                
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Upload error: {str(e)}"}
    
    def upload_file_from_streamlit(
        self,
        uploaded_file,
        is_baseline: bool = False,
        description: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        Upload a file from Streamlit's UploadedFile object
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            is_baseline: Whether to set as baseline
            description: Optional description
            
        Returns:
            Tuple of (success, response_data)
        """
        try:
            files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
            data = {
                'is_baseline': str(is_baseline).lower(),
                'description': description or ''
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/upload_data",
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Upload error: {str(e)}"}
    
    def list_uploads(self) -> Tuple[bool, Dict]:
        """
        Get list of all uploaded files
        
        Returns:
            Tuple of (success, response_data with 'files' list)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/list_uploads",
                timeout=30
            )
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Error listing uploads: {str(e)}"}
    
    def get_file_metadata(self, file_id: str) -> Tuple[bool, Dict]:
        """
        Get detailed metadata for a specific file
        
        Args:
            file_id: File identifier
            
        Returns:
            Tuple of (success, metadata_dict)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/get_file_metadata/{file_id}",
                timeout=30
            )
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Error getting metadata: {str(e)}"}
    
    def delete_upload(self, file_id: str) -> Tuple[bool, Dict]:
        """
        Delete an uploaded file
        
        Args:
            file_id: File identifier to delete
            
        Returns:
            Tuple of (success, response_data)
        """
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/delete_upload/{file_id}",
                timeout=30
            )
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Error deleting file: {str(e)}"}
    
    def list_baselines(self) -> Tuple[bool, Dict]:
        """
        Get list of all baseline versions
        
        Returns:
            Tuple of (success, response_data with 'baselines' list)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/list_baselines",
                timeout=30
            )
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Error listing baselines: {str(e)}"}
    
    def get_baseline(self, version_id: str) -> Tuple[bool, Dict]:
        """
        Get baseline information for a specific version
        
        Args:
            version_id: Baseline version identifier
            
        Returns:
            Tuple of (success, baseline_data)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/get_baseline/{version_id}",
                timeout=30
            )
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Error getting baseline: {str(e)}"}
    
    def check_quality(
        self,
        file_id: Optional[str] = None,
        file_path: Optional[Path] = None,
        check_missing: bool = True,
        check_duplicates: bool = True,
        check_outliers: bool = True,
        outlier_method: str = 'iqr'
    ) -> Tuple[bool, Dict]:
        """
        Run quality check on a dataset
        
        Args:
            file_id: File identifier (for existing upload)
            file_path: Path to new file
            check_missing: Check missing values
            check_duplicates: Check duplicates
            check_outliers: Check outliers
            outlier_method: Outlier detection method
            
        Returns:
            Tuple of (success, response_data)
        """
        try:
            data = {
                'check_missing': str(check_missing).lower(),
                'check_duplicates': str(check_duplicates).lower(),
                'check_outliers': str(check_outliers).lower(),
                'outlier_method': outlier_method
            }
            
            if file_id:
                data['file_id'] = file_id
                files = None
            elif file_path:
                with open(file_path, 'rb') as f:
                    files = {'file': (file_path.name, f)}
                    response = requests.post(
                        f"{self.base_url}/api/v1/check_quality",
                        files=files,
                        data=data,
                        timeout=self.timeout
                    )
                return self._handle_response(response)
            else:
                return False, {"detail": "Either file_id or file_path must be provided"}
            
            response = requests.post(
                f"{self.base_url}/api/v1/check_quality",
                data=data,
                timeout=self.timeout
            )
            
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Quality check error: {str(e)}"}
    
    def check_quality_from_streamlit(
        self,
        uploaded_file,
        check_missing: bool = True,
        check_duplicates: bool = True,
        check_outliers: bool = True,
        outlier_method: str = 'iqr'
    ) -> Tuple[bool, Dict]:
        """
        Run quality check on Streamlit uploaded file
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            check_missing: Check missing values
            check_duplicates: Check duplicates
            check_outliers: Check outliers
            outlier_method: Outlier detection method
            
        Returns:
            Tuple of (success, response_data)
        """
        try:
            files = {'file': (uploaded_file.name, uploaded_file.getvalue())}
            data = {
                'check_missing': str(check_missing).lower(),
                'check_duplicates': str(check_duplicates).lower(),
                'check_outliers': str(check_outliers).lower(),
                'outlier_method': outlier_method
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/check_quality",
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Quality check error: {str(e)}"}
    
    def get_quality_report(self, report_id: str) -> Tuple[bool, Dict]:
        """
        Get quality report by ID
        
        Args:
            report_id: Report identifier
            
        Returns:
            Tuple of (success, report_data)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/quality_report/{report_id}",
                timeout=30
            )
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Error getting report: {str(e)}"}
    
    def get_quality_summary(self, file_id: str) -> Tuple[bool, Dict]:
        """
        Get quick quality summary for a file
        
        Args:
            file_id: File identifier
            
        Returns:
            Tuple of (success, summary_data)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/quality_summary/{file_id}",
                timeout=30
            )
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Error getting summary: {str(e)}"}
    
    def list_quality_reports(self) -> Tuple[bool, Dict]:
        """
        List all quality reports
        
        Returns:
            Tuple of (success, reports_list)
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/list_quality_reports",
                timeout=30
            )
            return self._handle_response(response)
            
        except Exception as e:
            return False, {"detail": f"Error listing reports: {str(e)}"}


# Convenience function
_api_client = None

def get_api_client() -> APIClient:
    """
    Get singleton APIClient instance
    
    Returns:
        APIClient instance
    """
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client