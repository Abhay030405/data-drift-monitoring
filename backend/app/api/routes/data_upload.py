from fastapi import APIRouter, UploadFile, HTTPException
from backend.app.utils.file_handler import save_uploaded_file

router = APIRouter()

@router.post("/upload_data")
async def upload_data(file: UploadFile):
    try:
        metadata = save_uploaded_file(file)
        return {"status": "success", "metadata": metadata}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
