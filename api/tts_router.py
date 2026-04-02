import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.tts_service import tts_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nyaya", tags=["TTS"])


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Convert legal analysis text to speech.
    Uses Coqui XTTS v2 (local) with gTTS as fallback.
    Returns an audio stream (mp3 or wav).
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        audio_stream = tts_manager.generate_audio_stream(
            text=request.text.strip(),
            language=request.language
        )
        # Detect format: gTTS returns mp3, XTTS returns wav
        # Check first bytes for WAV signature
        header = audio_stream.read(4)
        audio_stream.seek(0)

        if header[:4] == b"RIFF":
            media_type = "audio/wav"
        else:
            media_type = "audio/mpeg"

        return StreamingResponse(
            audio_stream,
            media_type=media_type,
            headers={
                "Content-Disposition": "inline; filename=nyaya_tts.audio",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except RuntimeError as e:
        logger.error(f"TTS generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected TTS error: {e}")
        raise HTTPException(status_code=500, detail="Internal TTS error.")
