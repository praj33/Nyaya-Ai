import os
import io
import logging
import torch
from gtts import gTTS
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.xtts_model = None
        self.use_gpu = torch.cuda.is_available()
        self.model_loaded = False
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        # Directory for temporary files
        self.temp_dir = os.path.join(os.getcwd(), "temp_audio")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def _load_model(self):
        """Lazily load the XTTS v2 model."""
        if self.model_loaded:
            return True
        
        try:
            # Check if XTTS is available
            from TTS.api import TTS
            logger.info(f"Attempting to load XTTS v2 model (GPU: {self.use_gpu})...")
            
            # This will download the model if not present (~2GB)
            self.xtts_model = TTS(self.model_name).to("cuda" if self.use_gpu else "cpu")
            self.model_loaded = True
            logger.info("XTTS v2 model loaded successfully.")
            return True
        except ImportError:
            logger.error("TTS package not fully installed or compatible. Falling back to gTTS.")
            return False
        except Exception as e:
            logger.error(f"Failed to load XTTS v2 model: {e}")
            return False

    def generate_audio_stream(self, text: str, language: str = "en") -> io.BytesIO:
        """
        Generates audio for the given text.
        Tries Coqui XTTS v2 first, then falls back to gTTS.
        """
        # Cleanup long text for TTS processing (limit to reasonable chunk)
        clean_text = text[:1000] if len(text) > 1000 else text
        
        # 1. Try Local XTTS v2
        if self._load_model():
            try:
                logger.info("Generating audio with local Coqui XTTS v2...")
                temp_file = os.path.join(self.temp_dir, f"tts_out_{os.getpid()}.wav")
                
                # XTTS v2 requires a speaker_wav or speaker name. 
                # We'll use a default if possible or fallback.
                # For now, we'll try to generate with default settings.
                self.xtts_model.tts_to_file(
                    text=clean_text,
                    file_path=temp_file,
                    speaker="Ana Ciara", # A default speaker in XTTS v2
                    language=language
                )
                
                audio_data = io.BytesIO()
                with open(temp_file, "rb") as f:
                    audio_data.write(f.read())
                
                # Cleanup
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
                audio_data.seek(0)
                return audio_data
            except Exception as e:
                logger.warning(f"XTTS generation failed: {e}. Falling back to gTTS.")
        
        # 2. Fallback to gTTS (Cloud-based, very reliable)
        try:
            logger.info("Generating audio with gTTS (fallback)...")
            tts = gTTS(text=clean_text, lang=language)
            audio_data = io.BytesIO()
            tts.write_to_fp(audio_data)
            audio_data.seek(0)
            return audio_data
        except Exception as e:
            logger.error(f"Both XTTS and gTTS failed: {e}")
            raise RuntimeError("TTS generation failed completely.")

# Singleton instance
tts_manager = TTSService()
