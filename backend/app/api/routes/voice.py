import os
import asyncio
import logging
import time
import tempfile

# Ensure ffmpeg is in PATH for whisper without requiring terminal restart
ffmpeg_path = r"C:\Users\IT INFOTECH\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin"
if ffmpeg_path not in os.environ.get("PATH", ""):
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import whisper
import edge_tts

logger = logging.getLogger(__name__)
router = APIRouter()

# Global whisper model cache to avoid reloading
whisper_model = None

# A simple lock object to prevent concurrent loading logic if requests spam
_load_lock = asyncio.Lock()

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        logger.info("Loading Whisper 'base' model for the first time... this may take a moment.")
        try:
            # Load small base model for quick local inference
            whisper_model = whisper.load_model("base")
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load whisper model: {e}")
            raise e
    return whisper_model

class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-ChristopherNeural" # High quality male voice

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Accepts an audio file upload, saves temporarily, and runs local Whisper transcription."""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
        
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, f"jarvis_audio_{time.time()}.webm")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Save uploaded file
        content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(content)
            
        # Get model (loads on first request)
        model = get_whisper_model()
        
        # Run inference using the thread pool (since whisper is synchronous and blocks)
        logger.info(f"Transcribing audio file: {temp_file_path}")
        result = await asyncio.to_thread(model.transcribe, temp_file_path, fp16=False)
        
        transcribed_text = result.get("text", "").strip()
        logger.info(f"Transcription complete: '{transcribed_text}'")
        
        return {"text": transcribed_text}
        
    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Cleanup temp file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass

@router.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """Takes text and streams back MP3 audio using edge-tts."""
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
        
    try:
        logger.info(f"Synthesizing text: '{text[:30]}...' with voice {request.voice}")
        communicate = edge_tts.Communicate(text, request.voice)
        
        # Generator to stream the audio chunks directly
        async def audio_stream():
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]

        return StreamingResponse(audio_stream(), media_type="audio/mpeg")
        
    except Exception as e:
        logger.error(f"Error during synthesis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
