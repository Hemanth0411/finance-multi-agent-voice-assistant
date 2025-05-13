import sys
import os

# Add project root to sys.path to allow finding data_ingestion
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
import whisper
import tempfile
import shutil
from TTS.api import TTS
from dotenv import load_dotenv
import time
import logging
from data_ingestion.data_utils import log_duration

load_dotenv()

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
    print("Loading models...")
    try:
        stt_model = whisper.load_model(WHISPER_MODEL_NAME)
        print(f"Whisper model '{WHISPER_MODEL_NAME}' loaded.")
    except Exception as e:
        print(f"Error loading Whisper model: {e}. STT endpoint will not work.")
        # Depending on requirements, you might want to raise an error and stop startup

    try:
        tts_model = TTS(model_name=TTS_MODEL_NAME, progress_bar=True, gpu=False) # Set gpu=True if you have CUDA setup
        print(f"Coqui TTS model '{TTS_MODEL_NAME}' loaded.")
    except Exception as e:
        print(f"Error loading Coqui TTS model: {e}. TTS endpoint will not work.")
        # Handle potential download errors or missing model files

    # Create temp directory if it doesn't exist
    os.makedirs(TEMP_DIR, exist_ok=True)
    print("Models loaded.")

@app.on_event("shutdown")
async def cleanup():
    # Clean up temporary files on shutdown (optional)
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        print(f"Cleaned up temp directory: {TEMP_DIR}")


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
    
    stt_total_req_start_time = time.time() # Start total STT request timer

    # Use a temporary file to store the uploaded audio
    try:
        with tempfile.NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix=os.path.splitext(audio_file.filename)[1]) as temp_audio:
            shutil.copyfileobj(audio_file.file, temp_audio)
            temp_audio_path = temp_audio.name
        print(f"Temporary audio file saved at: {temp_audio_path}")

    except Exception as e:
         print(f"Error saving uploaded file: {e}")
         raise HTTPException(status_code=400, detail=f"Could not save uploaded file: {e}")
    finally:
         # Ensure the file object is closed
         await audio_file.close()

    try:
        # Perform transcription
        stt_transcribe_start_time = time.time()
        result = stt_model.transcribe(temp_audio_path)
        log_duration("STT_Whisper_Transcribe", stt_transcribe_start_time)
        transcribed_text = result["text"]
        print(f"Transcription result: {transcribed_text}")
        log_duration("STT_Total_Request", stt_total_req_start_time) # Log total STT request time
        return STTResponse(text=transcribed_text)

    except Exception as e:
        print(f"Error during transcription: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")
    finally:
        # Clean up the temporary file
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            print(f"Removed temporary audio file: {temp_audio_path}")


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

    tts_total_req_start_time = time.time() # Start total TTS request timer

    try:
        # Create a temporary file path for the output audio
        # Using NamedTemporaryFile ensures cleanup even if errors occur elsewhere
        # Suffix is important for potential file type recognition
        with tempfile.NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix=".wav") as temp_audio:
             output_wav_path = temp_audio.name

        print(f"Synthesizing text: '{request.text}'")
        print(f"Outputting to temporary file: {output_wav_path}")

        # Perform TTS synthesis
        tts_generate_start_time = time.time()
        tts_model.tts_to_file(text=request.text, file_path=output_wav_path)
        log_duration("TTS_Coqui_Generate", tts_generate_start_time)

        if not os.path.exists(output_wav_path) or os.path.getsize(output_wav_path) == 0:
             raise RuntimeError("TTS synthesis failed to produce an output file.")

        print(f"TTS synthesis complete. Audio saved at: {output_wav_path}")
        log_duration("TTS_Total_Request", tts_total_req_start_time) # Log total TTS request time

        # Return the generated WAV file
        # FileResponse will handle streaming the file and cleanup after sending
        return FileResponse(path=output_wav_path, media_type="audio/wav", filename="synthesized_speech.wav")

    except Exception as e:
        print(f"Error during TTS synthesis: {e}")
        # Clean up the potentially created (but possibly empty) temp file on error
        if 'output_wav_path' in locals() and os.path.exists(output_wav_path):
             try:
                 os.remove(output_wav_path)
                 print(f"Cleaned up failed TTS output file: {output_wav_path}")
             except OSError as rm_error:
                 print(f"Error removing failed TTS output file {output_wav_path}: {rm_error}")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {e}")


if __name__ == "__main__":
    import uvicorn
    # Make sure ffmpeg is installed for Whisper.
    # Make sure Coqui TTS models are downloaded/available.
    # Check Coqui docs for torch/soundfile compatibility if needed.
    # Run using:
    # cd finance-assistant
    # uvicorn agents.voice_agent.app:app --reload --port 8005
    print("Running Voice Agent Service. Ensure models load correctly.")
    print(f"Access docs at http://localhost:8005/docs")
    uvicorn.run("agents.voice_agent.app:app", host="0.0.0.0", port=8005, reload=True) 