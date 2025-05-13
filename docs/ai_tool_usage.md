# AI Tool Usage Log

This document details the usage of AI tools, specifically the Gemini 2.5 Pro model integrated within the Cursor IDE, during the development of the Finance Assistant project.

## Introduction

The development process heavily utilized an AI pair programmer (Gemini 2.5 Pro via Cursor) to accelerate implementation based on the provided plan, tool lists, and assignment description. The AI assistant was used for a wide range of tasks, including but not limited to:

*   Generating boilerplate code for project structure, FastAPI microservices, and the Streamlit frontend.
*   Implementing core logic for various agents (e.g., data fetching with `yfinance`, RAG pipeline components, financial analysis placeholders, voice processing).
*   Integrating different components, ensuring proper communication flow between the Streamlit app, orchestrator, and individual agents.
*   Refining placeholder functions with actual implementations (e.g., setting up the FAISS vector store, integrating the Google Gemini LLM via Langchain).
*   Creating and managing dependencies in `requirements.txt` and `packages.txt` (for Streamlit Cloud).
*   Developing `Dockerfile` and `docker-compose.yml` configurations for containerizing the backend services.
*   Generating documentation drafts, including this log, the main `README.md`, and inline code comments.
*   Debugging code, analyzing error messages, and suggesting solutions for issues encountered during development and deployment.
*   Assisting in formulating deployment strategies and generating step-by-step deployment guides for different environments (Linux server, Streamlit Community Cloud).
*   Advising on best practices, such as splitting requirements for backend and frontend.

## Code Generation & Refinement Examples

*   **Initial Project Structure:** The directory layout and initial empty Python files were created based on the project plan using the AI assistant's file editing capabilities.
*   **FastAPI Agent Boilerplate:** The initial FastAPI apps for the API, Retriever, Analysis, Language, and Voice agents were generated with basic endpoints, Pydantic models for request/response validation, and `uvicorn` run commands.
*   **Data Ingestion (`api_agent.py`):** The `yfinance` data fetching logic was implemented and later refined to handle potential errors and data extraction more robustly.
*   **Streamlit UI (`streamlit_app/app.py`):** The basic UI layout, audio recorder integration, text input, and agent calling logic were generated. Session state management was added later with AI assistance to prevent re-running full processing on simple interactions.
*   **Retriever Agent (`retriever_agent.py`):** The initial NumPy placeholder for the vector index was replaced with a functional FAISS index implementation, including text embedding generation using `sentence-transformers` and semantic search logic.
*   **Analysis Agent (`analysis_agent.py`):** The mock exposure calculation was refined to use `marketCap` data from `yfinance` for a more representative (though still simplified) regional exposure analysis.
*   **Language Agent (`language_agent.py`):** Placeholder response generation was replaced with the integration of the `gemini-1.5-flash-latest` model using `langchain-google-genai`. This included crafting the prompt template, making asynchronous LLM calls, and parsing the output. The prompt was later centralized into `orchestrator/prompts.py`.
*   **Voice Agent (`voice_agent.py`):** Implementation of STT using `openai-whisper` and TTS using `TTS` (Coqui TTS), including handling of temporary audio files.
*   **Dockerfile & Docker Compose:** The AI assistant helped create the initial `Dockerfile` by selecting an appropriate base image (`python:3.10-slim`, later changed to `python:3.11`), adding commands to install system dependencies (`ffmpeg`, `build-essential`), copy project files, install Python requirements, and set the entry point. It also helped generate the `docker-compose.yml` file to define and link the multiple backend services, manage environment variables, and set up port mappings and volumes. This included splitting `requirements.txt` into a backend-specific version for a lighter image.
*   **Error Handling & Debugging:**
    *   Identified and helped resolve indentation errors in Python code.
    *   Analyzed tracebacks from `docker-compose` logs to pinpoint issues like missing system packages (`ffmpeg`, `portaudio19-dev`) or Python dependencies in the Docker environment.
    *   Assisted in debugging `FileNotFoundError` for `packages.txt` on Streamlit Cloud by confirming its correct location and purpose.
    *   Helped modify `streamlit_app/app.py` to correctly use environment variables for agent URLs when deployed.

## Documentation Examples

*   **`README.md`:** The AI assistant generated large portions of the `README.md`, including the project overview, architecture description, features list, initial setup instructions, framework comparisons, and placeholders for performance benchmarks and the architecture diagram. It significantly helped in structuring the detailed deployment steps for a Linux server and Streamlit Community Cloud.
*   **`docs/ai_tool_usage.md` (This file):** The initial structure and several sections of this log were drafted by the AI assistant.
*   **Inline Comments:** Suggested and added comments to clarify complex code sections.

## Prompts Used

Prompts provided to the AI assistant were generally iterative and conversational, building upon previous interactions. Examples include:

*   Initial high-level: "Implement the finance assistant project based on Assignment.txt and the provided plan."
*   Specific tasks: "Create the FastAPI endpoint for the API agent to fetch stock data using yfinance."
*   Refinement: "Refine the Retriever Agent to use FAISS instead of a NumPy placeholder."
*   Integration: "Update the Orchestrator to call the Analysis Agent and then the Language Agent."
*   Containerization: "Generate a Dockerfile for the backend services. Use python 3.11-slim and include ffmpeg." "Create a docker-compose.yml to run all backend agents and the orchestrator."
*   Deployment: "Guide me step-by-step to deploy the backend to a DigitalOcean droplet and the frontend to Streamlit Cloud." "The Streamlit app is failing on Streamlit Cloud with a FileNotFoundError for packages.txt, what could be the issue?"
*   Documentation: "Update the README.md with the deployment steps we just discussed." "Generate a performance benchmark section for the README." "Update this ai_tool_usage.md based on our recent work."

## Model Parameters

*   **Primary Assistant:** Gemini 2.5 Pro (via Cursor IDE)
*   **Language Agent LLM:** Google Gemini (`gemini-1.5-flash-latest` via `langchain-google-genai`, configurable via `GEMINI_MODEL_NAME` environment variable).

*(This log aims to be representative. Specific code diffs or a more exhaustive list of prompts are not included for brevity but reflect a continuous pair-programming interaction.)* 