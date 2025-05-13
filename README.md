# 🎙️ Finance Assistant

A multi-source, multi-agent finance assistant that delivers spoken market briefs via a Streamlit app.

## Overview

This project implements a sophisticated financial assistant capable of answering questions about market data, risk exposure, and earnings surprises. It utilizes a microservice architecture with specialized agents for different tasks, including data ingestion, retrieval-augmented generation (RAG), analysis, language synthesis, and voice interaction.

**Use Case:** Morning Market Brief (Example)
> *User (Voice/Text):* "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises?"
> *System (Voice/Text):* "Today, your Asia tech allocation is [Calculated %] of the analyzed assets. TSMC reported strong earnings, beating analyst expectations significantly. Samsung Electronics provided mixed guidance, citing chip division challenges but strong mobile sales. Regional sentiment is neutral with a cautionary tilt due to rising yields."

## Architecture

The system follows a microservice architecture orchestrated via FastAPI:

1.  **Streamlit Frontend (`streamlit_app`):** Handles user interaction (voice/text input) and presents the final response (text/voice output).
2.  **Orchestrator (`orchestrator`):** Receives requests from the frontend, calls relevant agents in sequence, and aggregates results.
3.  **Agents (`agents`):** Specialized FastAPI services:
    *   **API Agent:** Fetches real-time/historical market data (using `yfinance`).
    *   **Retriever Agent:** Performs semantic search over a document store (using `sentence-transformers` and `faiss-cpu`) to find relevant context (e.g., earnings call snippets, news).
    *   **Analysis Agent:** Calculates financial metrics (e.g., regional risk exposure based on market cap).
    *   **Language Agent:** Synthesizes natural language responses using an LLM (configured for Google Gemini via `langchain-google-genai`) based on retrieved context and analysis.
    *   **Voice Agent:** Handles Speech-to-Text (using `openai-whisper`) and Text-to-Speech (using `TTS - Coqui TTS`).
4.  **Data Ingestion (`data_ingestion`):** Contains scripts for fetching data (currently `yfinance` interaction). (Scraping agent not yet implemented).

**Architecture Diagram:**

**[PLACEHOLDER: INSERT ARCHITECTURE DIAGRAM IMAGE HERE]**

*(A visual diagram should illustrate the flow:
Streamlit UI <--> Orchestrator
Orchestrator <--> API Agent
Orchestrator <--> Retriever Agent
Orchestrator <--> Analysis Agent
Orchestrator <--> Language Agent
Streamlit UI <--> Voice Agent (STT/TTS)
Orchestrator --> Language Agent --> Orchestrator --> Streamlit UI --> Voice Agent (TTS)
)*

*   User interacts (voice/text) with Streamlit UI.
*   Streamlit sends audio to Voice Agent (STT) or text directly to Orchestrator.
*   Orchestrator receives the query text.
*   Orchestrator calls API Agent and Retriever Agent concurrently.
*   Orchestrator calls Analysis Agent with market data.
*   Orchestrator calls Language Agent with query, context, market data, and analysis.
*   Language Agent returns synthesized text narrative to Orchestrator.
*   Orchestrator returns the full response (including narrative) to Streamlit.
*   Streamlit displays the text narrative.
*   Streamlit sends the narrative to Voice Agent (TTS).
*   Voice Agent returns audio.
*   Streamlit plays the audio response.

## Features

*   Voice and Text input/output.
*   Real-time market data retrieval.
*   Retrieval-Augmented Generation (RAG) for contextual information.
*   Basic portfolio risk analysis (regional exposure).
*   LLM-powered natural language response synthesis.
*   Modular microservice architecture using FastAPI.
*   Containerized deployment using Docker.

## Setup

**1. Prerequisites:**
*   Python 3.9+
*   Docker & Docker Compose (Recommended)
*   `ffmpeg` (Required by `openai-whisper`): Install via your system's package manager (e.g., `apt install ffmpeg`, `brew install ffmpeg`).
*   Git

**2. Clone the Repository:**
```bash
git clone <your-repository-url>
cd finance-assistant
```

**3. Install Dependencies:**
```bash
pip install -r requirements.txt
```
*Note: Installing `TTS` (Coqui TTS) might require specific `torch` versions depending on your system/CUDA setup. Refer to the [Coqui TTS Documentation](https://tts.readthedocs.io/en/latest/installation.html) if you encounter issues.*
*Note: The first time you run the Voice Agent, Coqui TTS may download the specified model files.*

**4. Environment Variables:**
Create a `.env` file in the project root directory (`finance-assistant/.env`) and add your API key:
```.env
# Required for Language Agent (Gemini)
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Override default models
# EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
# GEMINI_MODEL_NAME=gemini-1.5-flash-latest
# WHISPER_MODEL_NAME=base
# TTS_MODEL_NAME=tts_models/en/ljspeech/tacotron2-DDC
```
*Ensure the `.env` file is included in your `.gitignore`.*

**5. Running the Services:**

*   **Option A: Using Docker Compose (Recommended)**
    *(Dockerfile and docker-compose.yml to be finalized)*
    ```bash
    docker-compose up --build
    ```

*   **Option B: Running Manually (requires multiple terminals)**
    Navigate to the `finance-assistant` directory in each terminal.
    ```bash
    # Terminal 1: Orchestrator
    uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --reload

    # Terminal 2: API Agent
    uvicorn agents.api_agent.app:app --host 0.0.0.0 --port 8001 --reload

    # Terminal 3: Retriever Agent
    uvicorn agents.retriever_agent.app:app --host 0.0.0.0 --port 8002 --reload

    # Terminal 4: Analysis Agent
    uvicorn agents.analysis_agent.app:app --host 0.0.0.0 --port 8003 --reload

    # Terminal 5: Language Agent (Requires GOOGLE_API_KEY)
    uvicorn agents.language_agent.app:app --host 0.0.0.0 --port 8004 --reload

    # Terminal 6: Voice Agent (Requires ffmpeg, TTS model download)
    uvicorn agents.voice_agent.app:app --host 0.0.0.0 --port 8005 --reload

    # Terminal 7: Streamlit Frontend
    streamlit run streamlit_app/app.py
    ```

Access the frontend at `http://localhost:8501`. Agent API docs are available at their respective `/docs` endpoints (e.g., `http://localhost:8000/docs`).

## Deployment

Detailed deployment instructions will vary based on the chosen platform. Below are general guidelines and options:

**Option 1: Streamlit Community Cloud (Frontend Only)**
*   **Suitable for:** Deploying the Streamlit UI quickly for demos.
*   **Requires:** Agents running separately (e.g., locally via Docker, or on another cloud platform).
*   **Steps:**
    1.  Ensure your `streamlit_app/app.py` correctly points to the running agent URLs (using environment variables like `ORCHESTRATOR_URL`, `VOICE_AGENT_URL`).
    2.  Push your code (including `requirements.txt`) to a GitHub repository.
    3.  Connect your GitHub repo to [Streamlit Community Cloud](https://streamlit.io/cloud).
    4.  Configure required secrets (e.g., agent URLs) in the Streamlit Cloud settings.

**Option 2: Docker Compose on a Single VM/Server**
*   **Suitable for:** Simple, self-contained deployments.
*   **Requires:** A server (e.g., AWS EC2, DigitalOcean Droplet) with Docker and Docker Compose installed.
*   **Steps:**
    1.  Clone the repository onto the server.
    2.  Create the `.env` file with necessary API keys (`GOOGLE_API_KEY`).
    3.  Run `docker-compose up --build -d`.
    4.  Ensure the server's firewall allows traffic on the required ports (e.g., 8501 for Streamlit).
    5.  Access via `http://<server_ip>:8501`.

**Option 3: Container Orchestration Platform (Kubernetes, AWS ECS, Google Cloud Run)**
*   **Suitable for:** Scalable, resilient deployments.
*   **Requires:** Platform-specific configuration (e.g., Kubernetes YAML files, ECS Task Definitions, Cloud Run service definitions).
*   **Steps (General):**
    1.  Build Docker images for each service (or use the multi-stage `Dockerfile` if adapted) and push them to a container registry (Docker Hub, ECR, GCR).
    2.  Define deployment configurations for each service, specifying:
        *   Container image URI.
        *   Required environment variables (including `GOOGLE_API_KEY` and inter-agent URLs).
        *   Networking rules (allowing agents to communicate).
        *   Resource requests/limits.
        *   Potentially persistent volumes for FAISS index/cache if needed.
    3.  Deploy the configurations to your chosen platform.
    4.  Set up load balancers or ingress controllers to expose the Streamlit UI and potentially agent endpoints if needed externally.

**[PLACEHOLDER: ADD DETAILED STEPS FOR A SPECIFIC PLATFORM, e.g., Streamlit Cloud + Agents on EC2/Cloud Run]**

*   **Environment Variables:** Crucial step. Ensure `GOOGLE_API_KEY` and correct agent URLs are securely set in the chosen deployment environment.
*   **Persistent Storage:** The default FAISS index (`vector_store/faiss_index.bin`) is built/loaded at runtime. For production, you might want to pre-build it and load it from a persistent volume mounted into the Retriever Agent container.

## Framework/Toolkit Comparisons

*   **Web Framework (FastAPI vs. Flask/Django):** FastAPI was chosen for its native `async` support (crucial for I/O-bound agent calls), automatic data validation with Pydantic, and built-in interactive API documentation (Swagger UI), making it ideal for building performant microservices.
*   **Orchestration (LangChain vs. Custom Logic/LlamaIndex):** LangChain provides useful abstractions for building chains and integrating with LLMs, although currently, the primary orchestration logic resides within the FastAPI Orchestrator service using `httpx` for inter-service communication. LangChain is primarily used within the Language Agent for prompt templating and LLM interaction. LlamaIndex could be an alternative, particularly for more complex RAG pipelines.
*   **Frontend (Streamlit vs. Gradio/Flask+HTML):** Streamlit was chosen for its rapid UI development capabilities specifically tailored for data and AI applications, including built-in components like audio recorders and simplified state management.
*   **Vector Store (FAISS vs. Pinecone/ChromaDB):** FAISS was selected for its efficiency and local deployment capability (using `faiss-cpu`), avoiding external dependencies or costs associated with managed services like Pinecone, fulfilling the open-source requirement.
*   **Voice (Whisper/Coqui vs. Cloud Services):** OpenAI's Whisper (via `openai-whisper`) and Coqui TTS were chosen as powerful open-source options for STT and TTS, respectively, allowing for local execution and customization, though they require careful dependency management (`ffmpeg`, `torch`). Cloud-based voice services could offer simpler integration but might incur costs.

## Performance Benchmarks

*(Placeholder: Add results here after testing)*

*   **End-to-End Latency:** Measure time from user input (voice/text) to final response (voice/text).
    *   Target: < 5-10 seconds for typical queries.
*   **RAG Retrieval Speed:** Measure time taken by the Retriever Agent.
*   **STT/TTS Speed:** Measure transcription and synthesis time.
*   **LLM Response Time:** Measure time taken by the Language Agent.
*   **Resource Usage:** Monitor CPU/Memory usage of different agent containers under load.

## Demo

*(Link to Demo Video/GIF to be added)*

## AI Tool Usage

Details on the AI tools used during development (including prompts and generated code examples) can be found in [docs/ai_tool_usage.md](docs/ai_tool_usage.md). 