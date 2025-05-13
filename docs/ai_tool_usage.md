# AI Tool Usage Log

This document details the usage of AI tools, specifically the Gemini 2.5 Pro model integrated within the Cursor IDE, during the development of the Finance Assistant project.

## Introduction

The development process heavily utilized an AI pair programmer (Gemini 2.5 Pro via Cursor) to accelerate implementation based on the provided plan (`plan.md`), tool list (`tools.txt`), and assignment description (`Assignment.txt`). The AI assistant was used for:

*   Generating boilerplate code for project structure and FastAPI/Streamlit apps.
*   Implementing core logic for agents based on the plan (e.g., data fetching, RAG placeholders, analysis placeholders).
*   Integrating different components (e.g., connecting agents via the orchestrator).
*   Refining placeholder functions with actual implementations (e.g., FAISS index, Gemini LLM integration).
*   Generating documentation drafts (like this one and `README.md`).
*   Adding dependencies to `requirements.txt`.
*   Debugging and suggesting improvements.

## Code Generation Examples

*   **Initial Project Structure:** The directory layout and initial empty files were created based on `plan.md` using the AI assistant's file editing capabilities.
*   **FastAPI Agent Boilerplate:** The initial FastAPI apps for the API, Retriever, Analysis, Language, and Voice agents were generated with basic endpoints, Pydantic models, and `uvicorn` run commands.
*   **Data Ingestion (`api_agent.py`):** The `yfinance` data fetching logic was implemented based on the snippet in `plan.md`.
*   **Streamlit UI (`streamlit_app/app.py`):** The basic UI layout, audio recorder integration, and agent calling logic were generated.

## Refinement Examples

*   **Retriever Agent:** The initial NumPy placeholder for the vector index was replaced with a functional FAISS index implementation, including embedding generation and search logic.
*   **Analysis Agent:** The mock exposure calculation was refined to use `marketCap` data from `yfinance` for a more representative (though still simplified) analysis.
*   **Language Agent:** The placeholder response generation was replaced with the integration of the `gemini-1.5-flash-latest` model using `langchain-google-genai`, including prompt templating and asynchronous invocation.

## Prompts Used

Prompts provided to the AI assistant were generally high-level instructions based on the `plan.md` stages or specific refinement tasks. Examples include:

*   "Implement @plan.md using @tools.txt to complete @Assignment.txt"
*   "Implement the yfinance stock data fetching function."
*   "Create the FastAPI endpoint for the API agent."
*   "Implement the Analysis Agent FastAPI service with a placeholder exposure calculation."
*   "Integrate Analysis and Language agent calls into the orchestrator workflow."
*   "Implement the Voice Agent FastAPI service using Whisper and Coqui TTS."
*   "Implement the Streamlit UI with audio recorder, text input, and agent integration."
*   "Refine the placeholder functions (e.g., replacing the NumPy index in the Retriever, adding real analysis logic, configuring the actual LLM in the Language Agent). Use gemini-1.5-flash model"
*   "Start Day 3 tasks: Deployment and Documentation (README.md, docs/ai_tool_usage.md)."

## Model Parameters

*   **Primary Assistant:** Gemini 2.5 Pro (via Cursor)
*   **Language Agent LLM:** Google Gemini (`gemini-1.5-flash-latest` via `langchain-google-genai`, configurable via `GEMINI_MODEL_NAME` env var).

*(Further details, specific code diffs, or more granular prompt examples can be added as needed.)* 