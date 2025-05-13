import streamlit as st
from audiorecorder import audiorecorder
import requests
import io
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:8000")
VOICE_AGENT_URL = os.getenv("VOICE_AGENT_URL", "http://localhost:8005")

STT_ENDPOINT = f"{VOICE_AGENT_URL}/stt"
TTS_ENDPOINT = f"{VOICE_AGENT_URL}/tts"
PROCESS_QUERY_ENDPOINT = f"{ORCHESTRATOR_URL}/process_query"

# --- Initialize Session State ---
if 'last_query' not in st.session_state:
    st.session_state.last_query = None
if 'narrative' not in st.session_state:
    st.session_state.narrative = None
if 'audio_bytes' not in st.session_state:
    st.session_state.audio_bytes = None
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = None

# --- Helper Functions ---
def call_stt(audio_bytes):
    """Sends audio bytes to the STT service and returns the transcript."""
    if not audio_bytes:
        return None
    try:
        files = {'audio_file': ('audio.wav', audio_bytes, 'audio/wav')}
        response = requests.post(STT_ENDPOINT, files=files, timeout=60) # Increased timeout for STT
        response.raise_for_status()
        return response.json().get("text")
    except requests.exceptions.RequestException as e:
        st.error(f"STT request failed: {e}")
        return None
    except Exception as e:
        st.error(f"An error occurred during STT processing: {e}")
        return None

def call_orchestrator(query_text):
    """Sends text query to the orchestrator and returns the full response."""
    if not query_text:
        return None
    try:
        payload = {"query": query_text}
        response = requests.post(PROCESS_QUERY_ENDPOINT, json=payload, timeout=120) # Increased timeout for potentially long orchestrator calls
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Orchestrator request failed: {e}")
        return None
    except Exception as e:
        st.error(f"An error occurred during orchestrator processing: {e}")
        return None

def call_tts(text_to_speak):
    """Sends text to the TTS service and returns the audio bytes."""
    if not text_to_speak:
        return None
    try:
        payload = {"text": text_to_speak}
        response = requests.post(TTS_ENDPOINT, json=payload, timeout=60) # Increased timeout for TTS
        response.raise_for_status()
        return response.content # Return raw audio bytes
    except requests.exceptions.RequestException as e:
        st.error(f"TTS request failed: {e}")
        return None
    except Exception as e:
        st.error(f"An error occurred during TTS processing: {e}")
        return None

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")
st.title("🎙️ Finance Assistant")

st.write("Ask your financial question via voice or text below.")

col1, col2 = st.columns(2)

query_text = None
new_query_initiated = False

with col1:
    st.subheader("Record Audio Query:")
    audio = audiorecorder("Click to record", "Recording...")

    if len(audio) > 0:
        # Process audio only if it's different from the last processed one (optional)
        # This prevents re-processing if the page reruns without new recording.
        # Simple check based on length; a hash might be more robust.
        # if len(audio) != st.session_state.get('last_audio_len', 0):
        #     st.session_state.last_audio_len = len(audio)
        st.audio(audio.export().read(), format="audio/wav")
        with st.spinner("Transcribing audio..."):
            transcript = call_stt(audio.export().read())
            if transcript:
                st.write(f"**Transcribed Text:** {transcript}")
                if transcript != st.session_state.last_query: # Check if it's a new query
                    query_text = transcript
                    new_query_initiated = True
            else:
                st.warning("Transcription failed or returned empty.")
            # else:
            #     # Clear the stored length if transcription failed
            #     st.session_state.last_audio_len = 0

with col2:
    st.subheader("Or Enter Text Query:")
    text_input = st.text_input("Type your query here:", key="text_query")
    submit_button = st.button("Submit Text Query")

    if submit_button and text_input:
         if text_input != st.session_state.last_query: # Check if it's a new query
            query_text = text_input
            new_query_initiated = True

# --- Clear Previous Output if New Query --- 
if new_query_initiated:
    st.session_state.narrative = None
    st.session_state.audio_bytes = None
    st.session_state.raw_data = None
    st.session_state.last_query = query_text # Store the new query

# --- Processing Logic --- 
if query_text: # Only process if query_text was set (implies new_query_initiated was True)
    st.divider()
    st.subheader("Processing Request...")
    with st.spinner("Calling agents and generating response..."):
        orchestrator_response = call_orchestrator(query_text)

    if orchestrator_response:
        # Store results in session state
        st.session_state.narrative = orchestrator_response.get("final_narrative", "Error: No narrative generated.")
        st.session_state.raw_data = orchestrator_response
        
        # Generate audio only if narrative exists
        if st.session_state.narrative and not st.session_state.narrative.startswith("Error:"):
            with st.spinner("Synthesizing audio..."):
                audio_response_bytes = call_tts(st.session_state.narrative)
                st.session_state.audio_bytes = audio_response_bytes
        else:
             st.session_state.audio_bytes = None # Ensure no old audio plays if narrative fails

    else:
        st.error("Failed to get response from the orchestrator.")
        # Clear state in case of orchestrator failure
        st.session_state.narrative = "Error: Failed to get response from the orchestrator."
        st.session_state.audio_bytes = None
        st.session_state.raw_data = None

# --- Display Output Area (always present, content depends on session state) --- 
st.divider()
st.subheader("Response:")

if st.session_state.narrative:
    st.markdown(st.session_state.narrative)

    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/wav")
    elif not st.session_state.narrative.startswith("Error:"): # Don't show warning if narrative itself was error
        st.warning("Could not generate audio response.")

    if st.session_state.raw_data:
        with st.expander("Show Raw Data"):
            st.json(st.session_state.raw_data)

elif (submit_button and not text_input) and len(audio) == 0 and not st.session_state.narrative:
     st.warning("Please record audio or type a text query first.") 