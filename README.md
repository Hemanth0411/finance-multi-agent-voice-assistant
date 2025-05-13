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

[View on Eraser![](https://app.eraser.io/workspace/wmOtjFBSzgkJTGbMihF8/preview?elements=IBZoSlBhubLQhfLWyGaEWQ&type=embed)](https://app.eraser.io/workspace/wmOtjFBSzgkJTGbMihF8?elements=IBZoSlBhubLQhfLWyGaEWQ)

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

This section outlines the recommended approach for deploying the Finance Assistant:
*   **Backend FastAPI Agents:** Hosted on a Linux server (e.g., DigitalOcean Droplet) using Docker Compose.
*   **Frontend Streamlit App:** Hosted on Streamlit Community Cloud.

### Part 1: Deploying Backend Services to a Linux Server (e.g., DigitalOcean Droplet)

**1.1. Prepare the Server:**

*   **Connect via SSH:**
    ```bash
    ssh your_username@your_server_ip_address
    ```
*   **Update System:**
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```
*   **Install Docker:**
    Follow the official Docker installation guide for your distribution. For Debian/Ubuntu:
    ```bash
    sudo apt install apt-transport-https ca-certificates curl software-properties-common -y
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    sudo apt update
    sudo apt install docker-ce -y
    sudo systemctl status docker
    sudo usermod -aG docker ${USER} # Log out and back in for this to take effect
    ```
*   **Install Docker Compose:**
    Check the [Docker Compose releases page](https://github.com/docker/compose/releases) for the latest version.
    ```bash
    # Example for v2.27.0 (replace if newer exists)
    LATEST_COMPOSE_VERSION="v2.27.0"
    sudo curl -L "https://github.com/docker/compose/releases/download/${LATEST_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    docker-compose --version
    ```
*   **Configure Firewall (e.g., UFW on Ubuntu):**
    Allow SSH and the ports for the Orchestrator and Voice Agent.
    ```bash
    sudo ufw allow OpenSSH
    sudo ufw allow 8000/tcp # Orchestrator
    sudo ufw allow 8005/tcp # Voice Agent
    sudo ufw enable
    sudo ufw status
    ```
    (Adjust for your specific firewall or cloud provider's firewall settings).

**1.2. Deploy Backend Code:**

*   **Install Git (if needed):**
    ```bash
    sudo apt install git -y
    ```
*   **Clone Repository:**
    ```bash
    git clone <your-github-repository-url>
    cd finance-assistant
    ```
*   **Create `.env` file for Backend:**
    In the `finance-assistant` directory, create `.env`:
    ```bash
    nano .env
    ```
    Add the following, replacing placeholders:
    ```dotenv
    # finance-assistant/.env (on your server)

    GOOGLE_API_KEY=your_actual_google_api_key_here

    # URLs for inter-agent communication within the Docker network
    API_AGENT_URL=http://api_agent:8001
    RETRIEVER_AGENT_URL=http://retriever_agent:8002
    ANALYSIS_AGENT_URL=http://analysis_agent:8003
    LANGUAGE_AGENT_URL=http://language_agent:8004
    VOICE_AGENT_URL=http://voice_agent:8005
    ORCHESTRATOR_URL=http://orchestrator:8000
    ```
*   **Verify `Dockerfile` for Backend:**
    Ensure your `finance-assistant/Dockerfile` is configured for the backend:
    *   Uses a suitable Python version (e.g., `FROM python:3.11-slim`).
    *   Installs `build-essential` and `ffmpeg` system packages:
        ```dockerfile
        RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
        RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
        ```
    *   Uses a backend-specific requirements file (e.g., `requirements-backend.txt`) that excludes Streamlit and other frontend-only dependencies:
        ```dockerfile
        COPY requirements-backend.txt .
        RUN pip install --no-cache-dir -r requirements-backend.txt
        ```
        (You should create `requirements-backend.txt` by copying `requirements.txt` and removing frontend libraries like `streamlit`, `streamlit-audiorecorder`).

**1.3. Build and Run Backend Services:**

*   Navigate to the `finance-assistant` directory on your server.
*   Build and start the containers:
    ```bash
    docker-compose up --build -d
    ```
*   Monitor logs (optional):
    ```bash
    docker-compose logs -f
    # Or for specific services:
    # docker-compose logs -f orchestrator
    # docker-compose logs -f voice_agent
    ```
*   Verify containers are running:
    ```bash
    docker-compose ps
    ```
*   **Test public backend endpoints from your local machine:**
    *   Orchestrator docs: `http://<your_server_ip_address>:8000/docs`
    *   Voice Agent docs: `http://<your_server_ip_address>:8005/docs`
    Ensure these are accessible.

### Part 2: Deploying Frontend to Streamlit Community Cloud

**2.1. Prepare Your GitHub Repository:**

*   **`requirements.txt`:** Ensure the main `requirements.txt` file in the root of your repository contains all dependencies needed for the Streamlit app itself, including `streamlit`, `requests`, `audiorecorder`, and `python-dotenv`.
*   **`packages.txt`:** Create a `packages.txt` file in the root of your repository. This tells Streamlit Cloud to install system-level dependencies. For this project, it needs:
    ```txt
    # packages.txt
    portaudio19-dev
    ffmpeg
    ```
*   Commit and push `requirements.txt` and `packages.txt` to your GitHub repository.

**2.2. Deploy on Streamlit Community Cloud:**

*   Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
*   Click "New app".
*   **Repository:** Select your GitHub repository.
*   **Branch:** Choose your main branch (e.g., `main`).
*   **Main file path:** Set this to `streamlit_app/app.py`.
*   **Python version:** Select a Python version (e.g., 3.11, matching your backend if possible).
*   **Advanced settings... -> Secrets:**
    Configure the following secrets, replacing `<your_server_ip_address>` with the public IP of your server where the backend is running:
    *   `ORCHESTRATOR_URL`: `http://<your_server_ip_address>:8000`
    *   `VOICE_AGENT_URL`: `http://<your_server_ip_address>:8005`
*   Click "Deploy!".
*   Monitor the deployment logs on Streamlit Cloud. Once deployed, test the application using the provided Streamlit Cloud URL.

This provides a comprehensive deployment strategy. Remember to replace placeholders like `<your-github-repository-url>` and `<your_server_ip_address>`.

## Framework/Toolkit Comparisons

*   **Web Framework (FastAPI vs. Flask/Django):** FastAPI was chosen for its native `async` support (crucial for I/O-bound agent calls), automatic data validation with Pydantic, and built-in interactive API documentation (Swagger UI), making it ideal for building performant microservices.
*   **Orchestration (LangChain vs. Custom Logic/LlamaIndex):** LangChain provides useful abstractions for building chains and integrating with LLMs, although currently, the primary orchestration logic resides within the FastAPI Orchestrator service using `httpx` for inter-service communication. LangChain is primarily used within the Language Agent for prompt templating and LLM interaction. LlamaIndex could be an alternative, particularly for more complex RAG pipelines.
*   **Frontend (Streamlit vs. Gradio/Flask+HTML):** Streamlit was chosen for its rapid UI development capabilities specifically tailored for data and AI applications, including built-in components like audio recorders and simplified state management.
*   **Vector Store (FAISS vs. Pinecone/ChromaDB):** FAISS was selected for its efficiency and local deployment capability (using `faiss-cpu`), avoiding external dependencies or costs associated with managed services like Pinecone, fulfilling the open-source requirement.
*   **Voice (Whisper/Coqui vs. Cloud Services):** OpenAI's Whisper (via `openai-whisper`) and Coqui TTS were chosen as powerful open-source options for STT and TTS, respectively, allowing for local execution and customization, though they require careful dependency management (`ffmpeg`, `torch`). Cloud-based voice services could offer simpler integration but might incur costs.

## Performance Benchmarks

The following benchmarks were conducted on [Date - e.g., May 13, 2024] under the specified conditions. These are initial estimates based on available logs and can vary based on query complexity, network conditions, and underlying LLM performance.

**Testing Environment:**
*   **Backend:** Deployed via Docker Compose on a local Windows machine (for these specific logs) / Target: DigitalOcean Droplet.
*   **Frontend:** Streamlit Community Cloud / Local Streamlit instance.
*   **LLM Model:** `gemini-1.5-flash-latest` (as of test date).
*   **Test Queries:**
    *   *Simple Query (Text Example):* "What's the current price of GOOGL?" (or AAPL)
    *   *Complex Query (Voice Example):* "What's our risk exposure in Asia tech stocks today, and highlight any earnings surprises for major tech companies?" (as per original assignment)

**Latency Results (Representative values from logs):**

| Metric                        | Simple Query (Text) | Complex Query (Voice) | Notes                                                                 |
| :---------------------------- | :------------------: | :--------------------: | :-------------------------------------------------------------------- |
| **End-to-End Latency**        |        ~4.7s        |        ~10.5s         | Text: Streamlit UI to text response. Voice: Full voice-in/voice-out.    |
| STT Latency                   |         N/A         |         ~1.3s         | Whisper 'base' model.                                                 |
| API Agent Latency (per symbol)|        ~1.2s        |         ~1.2s         | `yfinance` calls (range ~0.9s-1.6s observed).                        |
| Retriever Agent Latency       |        ~0.04s       |         ~0.04s        | FAISS search (range ~20ms-60ms observed).                             |
| Analysis Agent Latency        |        ~0.0s        |         ~0.0s         | Negligible processing time after fix (was ~0.26s during an error state). |
| Language Agent (LLM) Latency  |        ~0.8s        |         ~0.9s         | Gemini Flash (range ~0.7s-2.5s observed).                            |
| TTS Latency                   |         N/A         |         ~3.5s         | Coqui TTS.                                                            |
| Orchestrator Processing       |        ~0.2s        |         ~0.3s         | Estimated core logic time, excluding agent `await` times.                |

*Note on "End-to-End Latency (Text)": This value (~4.7s) is taken from Streamlit's `E2E_Streamlit_Orchestrator_Response` log, representing the time from query submission in the UI to the orchestrator's full response being available to Streamlit. The sum of individual agent latencies above (~2.04s for a simple text query with one symbol) suggests the remaining time (~2.66s) is distributed among network calls between services, Orchestrator's internal `httpx` I/O and data handling, and Streamlit's processing.*

## Demo



## AI Tool Usage

Details on the AI tools used during development (including prompts and generated code examples) can be found in [docs/ai_tool_usage.md](docs/ai_tool_usage.md). 