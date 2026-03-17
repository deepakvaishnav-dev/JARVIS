import logging
import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from google import genai
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

TEMP_UPLOAD_DIR = "/tmp/jarvis_uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """
    Accepts a file, saves it temporarily, uploads it to Gemini, and returns the file ID.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(TEMP_UPLOAD_DIR, unique_filename)
    
    try:
        # Save uploaded file temporarily
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"Uploading {file.filename} to Gemini...")
        
        # Upload to Gemini
        gemini_file = client.files.upload(
            file=temp_path,
            display_name=file.filename
        )
        
        logger.info(f"Successfully uploaded {file.filename} as {gemini_file.name}")
        
        return {
            "success": True,
            "file_id": gemini_file.name,
            "filename": file.filename,
            "mime_type": gemini_file.mime_type
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {e}")
