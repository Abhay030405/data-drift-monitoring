"""
API Client for Neural Watch Frontend
Phase 1: Data Ingestion & Quality Setup
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


# Singleton instance
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