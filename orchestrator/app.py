from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Orchestrator Service",
    description="Routes requests to specialized agents and aggregates results.",
    version="0.1.0"
)

# Configuration for agent endpoints (Loaded from environment)
API_AGENT_URL = os.getenv("API_AGENT_URL", "http://localhost:8001")
RETRIEVER_AGENT_URL = os.getenv("RETRIEVER_AGENT_URL", "http://localhost:8002")
ANALYSIS_AGENT_URL = os.getenv("ANALYSIS_AGENT_URL", "http://localhost:8003")
LANGUAGE_AGENT_URL = os.getenv("LANGUAGE_AGENT_URL", "http://localhost:8004")

class QueryRequest(BaseModel):
    query: str
    # Example: Add specific parameters needed for different agents if necessary
    # symbols: list[str] = ["TSM", "005930.KS"] # Default symbols for market brief

class OrchestratorResponse(BaseModel):
    retrieved_context: list[dict]
    market_data: dict
    analysis_results: dict
    final_narrative: str

async def call_agent(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> dict:
    """Helper function to call another agent asynchronously."""
    try:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status() # Raise exception for 4xx/5xx errors
        return response.json()
    except httpx.RequestError as e:
        print(f"Error calling {url}: {e}")
        # Depending on criticality, might raise HTTPException or return default
        raise HTTPException(status_code=503, detail=f"Agent call failed: {e}")
    except httpx.HTTPStatusError as e:
        print(f"Error response {e.response.status_code} from {url}: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Agent error: {e.response.text}")

@app.post("/process_query", summary="Process User Query", description="Orchestrates agent calls to retrieve and process information based on the user query.")
async def process_query(request: QueryRequest):
    """Endpoint to handle user query orchestration."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Call Retriever Agent
        retriever_payload = {"query": request.query, "top_k": 3}
        retrieval_task = call_agent(client, "POST", f"{RETRIEVER_AGENT_URL}/retrieve", json=retriever_payload)

        # 2. Call API Agent (Example: Extract symbols from query or use defaults)
        #    For now, using fixed symbols as per plan example
        symbols_to_fetch = ["TSM", "005930.KS"]
        api_tasks = [call_agent(client, "GET", f"{API_AGENT_URL}/stock/{symbol}") for symbol in symbols_to_fetch]

        # Run API and Retriever tasks concurrently
        initial_results = await asyncio.gather(retrieval_task, *api_tasks, return_exceptions=True)

        # Process initial results and handle potential errors
        retrieved_data = None
        market_data_results = {}
        valid_market_data_for_analysis = {} # Store only successful results for analysis

        # Check retrieval result
        if isinstance(initial_results[0], Exception):
            print(f"Retriever agent call failed: {initial_results[0]}")
            raise HTTPException(status_code=500, detail="Failed to retrieve context.")
        else:
            # Ensure 'results' key exists, default to empty list
            retrieved_data = initial_results[0].get('results', []) if isinstance(initial_results[0], dict) else []

        # Check API agent results
        for i, symbol in enumerate(symbols_to_fetch):
            result = initial_results[i+1]
            if isinstance(result, Exception):
                print(f"API agent call failed for {symbol}: {result}")
                market_data_results[symbol] = {"error": f"Failed to fetch data for {symbol}"}
            elif isinstance(result, dict): # Check if result is a dict (successful fetch)
                 market_data_results[symbol] = result
                 valid_market_data_for_analysis[symbol] = result # Add successful fetches for analysis
            else:
                 # Handle unexpected result type
                 print(f"API agent call for {symbol} returned unexpected type: {type(result)}")
                 market_data_results[symbol] = {"error": "Unexpected response type from API agent"}

        # 3. Call Analysis Agent (if we have valid market data)
        analysis_results = {"error": "No valid market data for analysis"} # Default
        if valid_market_data_for_analysis:
             analysis_payload = {
                 "market_data": valid_market_data_for_analysis,
                 # Add portfolio AUM or holdings here if needed by analysis agent
                 "total_aum": 1_000_000 # Using default from analysis agent for now
             }
             try:
                 analysis_response = await call_agent(client, "POST", f"{ANALYSIS_AGENT_URL}/analyze", json=analysis_payload)
                 analysis_results = analysis_response # Store the full analysis result
             except HTTPException as e:
                  # Handle analysis agent failure - log and continue, maybe return partial results
                  print(f"Analysis agent call failed: {e.detail}")
                  analysis_results = {"error": f"Analysis agent failed: {e.detail}"}
             except Exception as e:
                  print(f"Unexpected error calling analysis agent: {e}")
                  analysis_results = {"error": f"Unexpected error during analysis call: {e}"}

        # 4. Call Language Agent
        language_payload = {
            "query": request.query,
            "retrieved_context": retrieved_data,
            "analysis_results": analysis_results, # Pass the whole dict
            "market_data": market_data_results # Pass all market data (including errors)
        }
        final_narrative = "Error: Failed to generate narrative." # Default
        try:
             language_response = await call_agent(client, "POST", f"{LANGUAGE_AGENT_URL}/synthesize", json=language_payload)
             final_narrative = language_response.get("narrative", "Error: No narrative content in response.")
        except HTTPException as e:
             print(f"Language agent call failed: {e.detail}")
             final_narrative = f"Error: Language agent failed: {e.detail}"
        except Exception as e:
             print(f"Unexpected error calling language agent: {e}")
             final_narrative = f"Error: Unexpected error during language agent call: {e}"

    # Combine all results for the final response
    return OrchestratorResponse(
        retrieved_context=retrieved_data,
        market_data=market_data_results,
        analysis_results=analysis_results,
        final_narrative=final_narrative
    )

if __name__ == "__main__":
    import uvicorn
    # Run using:
    # cd finance-assistant
    # uvicorn orchestrator.app:app --reload --port 8000
    print("Running Orchestrator Service. Access docs at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)