from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import whisper
import tempfile
import os
import shutil
from TTS.api import TTS
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voice Agent Service",
    description="Handles Speech-to-Text (STT) and Text-to-Speech (TTS).",
    version="0.1.0"
)

# --- Configuration ---
# Choose Whisper model (e.g., tiny, base, small, medium, large)
# Smaller models are faster but less accurate.
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "base")
# Choose Coqui TTS model (ensure it's downloaded/available)
# Example: "tts_models/en/ljspeech/tacotron2-DDC"
# List available models via `tts --list_models`
TTS_MODEL_NAME = os.getenv("TTS_MODEL_NAME", "tts_models/en/ljspeech/tacotron2-DDC")
TEMP_DIR = "./temp_audio"

# --- Model Loading ---
# Load models once when the application starts
stt_model = None
tts_model = None

@app.on_event("startup")
async def load_models():
    global stt_model, tts_model
    logger.info("Loading STT and TTS models...")
    try:
        stt_model = whisper.load_model(WHISPER_MODEL_NAME)
        logger.info(f"Whisper STT model '{WHISPER_MODEL_NAME}' loaded.")
    except Exception as e:
        logger.error(f"Error loading Whisper STT model: {e}. STT endpoint will be impaired.", exc_info=True)

    try:
        tts_model = TTS(model_name=TTS_MODEL_NAME, progress_bar=False, gpu=False) # Set progress_bar=False for cleaner logs
        logger.info(f"Coqui TTS model '{TTS_MODEL_NAME}' loaded.")
    except Exception as e:
        logger.error(f"Error loading Coqui TTS model: {e}. TTS endpoint will be impaired.", exc_info=True)

    os.makedirs(TEMP_DIR, exist_ok=True)
    logger.info("Model loading process complete.")

@app.on_event("shutdown")
async def cleanup():
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
            logger.info(f"Cleaned up temporary directory: {TEMP_DIR}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory {TEMP_DIR}: {e}", exc_info=True)


# --- Pydantic Models ---
class STTResponse(BaseModel):
    text: str

class TTSRequest(BaseModel):
    text: str

# --- Endpoints ---
@app.post("/stt", response_model=STTResponse, summary="Speech-to-Text", description="Converts spoken audio file to text using Whisper.")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """Endpoint for Speech-to-Text.

    Args:
        audio_file: The uploaded audio file (e.g., WAV, MP3).

    Returns:
        STTResponse containing the transcribed text.

    Raises:
        HTTPException: 500 if STT model failed to load or transcription fails.
                       400 if file upload fails.
    """
    if not stt_model:
        raise HTTPException(status_code=500, detail="STT model not loaded.")

    # Use a temporary file to store the uploaded audio
    try:
        with tempfile.NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix=os.path.splitext(audio_file.filename)[1]) as temp_audio:
            shutil.copyfileobj(audio_file.file, temp_audio)
            temp_audio_path = temp_audio.name
        logger.debug(f"Temporary audio file for STT saved at: {temp_audio_path}")

    except Exception as e:
         logger.error(f"Error saving STT uploaded file: {e}", exc_info=True)
         raise HTTPException(status_code=400, detail=f"Could not save uploaded file: {e}")
    finally:
         # Ensure the file object is closed
         await audio_file.close()

    try:
        # Perform transcription
        result = stt_model.transcribe(temp_audio_path)
        transcribed_text = result["text"]
<<<<<<< Updated upstream
        print(f"Transcription result: {transcribed_text}")
=======
        logger.info(f"STT Transcription result: {transcribed_text[:50]}...")
        log_duration("STT_Total_Request", stt_total_req_start_time)
>>>>>>> Stashed changes
        return STTResponse(text=transcribed_text)

    except Exception as e:
        logger.error(f"Error during STT transcription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        # Clean up the temporary file
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            logger.debug(f"Removed temporary STT audio file: {temp_audio_path}")


@app.post("/tts", response_class=FileResponse, summary="Text-to-Speech", description="Converts text to spoken audio using Coqui TTS.")
async def text_to_speech(request: TTSRequest):
    """Endpoint for Text-to-Speech.

    Args:
        request: TTSRequest containing the text to synthesize.

    Returns:
        FileResponse containing the synthesized audio (WAV format).

    Raises:
        HTTPException: 500 if TTS model failed to load or synthesis fails.
                       400 if input text is empty.
    """
    if not tts_model:
        raise HTTPException(status_code=500, detail="TTS model not loaded.")

    if not request.text or not request.text.strip():
         raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    try:
        # Create a temporary file path for the output audio
        # Using NamedTemporaryFile ensures cleanup even if errors occur elsewhere
        # Suffix is important for potential file type recognition
        with tempfile.NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix=".wav") as temp_audio:
             output_wav_path = temp_audio.name

        logger.info(f"Synthesizing TTS for text: '{request.text[:50]}...'")
        logger.debug(f"Outputting TTS to temporary file: {output_wav_path}")

        # Perform TTS synthesis
        # Ensure the file path exists before calling tts_to_file
        tts_model.tts_to_file(text=request.text, file_path=output_wav_path)

        if not os.path.exists(output_wav_path) or os.path.getsize(output_wav_path) == 0:
             logger.error("TTS synthesis failed to produce a non-empty output file.")
             raise RuntimeError("TTS synthesis failed to produce an output file.")

<<<<<<< Updated upstream
        print(f"TTS synthesis complete. Audio saved at: {output_wav_path}")
=======
        logger.info(f"TTS synthesis complete. Audio saved at: {output_wav_path}")
        log_duration("TTS_Total_Request", tts_total_req_start_time)
>>>>>>> Stashed changes

        # Return the generated WAV file
        # FileResponse will handle streaming the file and cleanup after sending
        return FileResponse(path=output_wav_path, media_type="audio/wav", filename="synthesized_speech.wav")

    except Exception as e:
        logger.error(f"Error during TTS synthesis: {e}", exc_info=True)
        # Clean up the potentially created (but possibly empty) temp file on error
        if 'output_wav_path' in locals() and os.path.exists(output_wav_path):
             try:
                 os.remove(output_wav_path)
                 logger.warning(f"Cleaned up failed TTS output file: {output_wav_path}")
             except OSError as rm_error:
                 logger.error(f"Error removing failed TTS output file {output_wav_path}: {rm_error}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {e}")


# Removed if __name__ == "__main__" block for deployment
# if __name__ == "__main__":
#     import uvicorn
#     # logger.info("Running Voice Agent Service. Ensure models load correctly.")
#     # logger.info(f"Access docs at http://localhost:8005/docs")
#     uvicorn.run("agents.voice_agent.app:app", host="0.0.0.0", port=8005, reload=True) 