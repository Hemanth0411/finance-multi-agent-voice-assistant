from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
import os
from dotenv import load_dotenv
<<<<<<< Updated upstream
=======
import time
import logging
import sys # Added for path modification
# Add project root to sys.path
PROJECT_ROOT_ORCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # orchestrator is one level down from root
if PROJECT_ROOT_ORCH not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_ORCH)

# Ensure data_utils is in python path or adjust import
from data_ingestion.data_utils import log_duration 

logger = logging.getLogger(__name__) # Added
>>>>>>> Stashed changes

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
        logger.error(f"Error calling agent at {url}: {e}", exc_info=True) # Changed from print
        raise HTTPException(status_code=503, detail=f"Agent call failed: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Error response {e.response.status_code} from agent at {url}: {e.response.text}", exc_info=True) # Changed from print
        raise HTTPException(status_code=e.response.status_code, detail=f"Agent error: {e.response.text}")

@app.post("/process_query", summary="Process User Query", description="Orchestrates agent calls to retrieve and process information based on the user query.")
async def process_query(request: QueryRequest):
    """Endpoint to handle user query orchestration."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Call Retriever Agent
        retriever_payload = {"query": request.query, "top_k": 3}
        retrieval_task = call_agent(client, "POST", f"{RETRIEVER_AGENT_URL}/retrieve", json=retriever_payload)

<<<<<<< Updated upstream
        # 2. Call API Agent (Example: Extract symbols from query or use defaults)
        #    For now, using fixed symbols as per plan example
        symbols_to_fetch = ["TSM", "005930.KS"]
        api_tasks = [call_agent(client, "GET", f"{API_AGENT_URL}/stock/{symbol}") for symbol in symbols_to_fetch]
=======
        # 2. Call API Agent
        # --- Symbol extraction from query ---
        import re

        COMPANY_NAME_TO_SYMBOL_MAP = {
            "GOOGLE": "GOOGL",
            "ALPHABET": "GOOGL",
            "APPLE": "AAPL",
            "MICROSOFT": "MSFT",
            "AMAZON": "AMZN",
            "TESLA": "TSLA",
            "NVIDIA": "NVDA",
            "META": "META",
            "FACEBOOK": "META",
            "BERKSHIRE HATHAWAY": "BRK-B",
            "JPMORGAN CHASE": "JPM",
            "JPMORGAN": "JPM",
            "JOHNSON & JOHNSON": "JNJ",
            "JOHNSON AND JOHNSON": "JNJ",
            "VISA": "V",
            "MASTERCARD": "MA",
            "PROCTER & GAMBLE": "PG",
            "PROCTER AND GAMBLE": "PG",
            "NETFLIX": "NFLX",
            "SALESFORCE": "CRM",
            "ADOBE": "ADBE",
            "INTEL": "INTC",
            "CISCO": "CSCO",
            "ORACLE": "ORCL",
            "WALMART": "WMT",
            "BANK OF AMERICA": "BAC",
            "EXXONMOBIL": "XOM",
            "EXXON": "XOM",
            "UNITEDHEALTH": "UNH",
            "UNITED HEALTH": "UNH",
            "HOME DEPOT": "HD",
            "DISNEY": "DIS",
            "WALT DISNEY": "DIS",
            "CHEVRON": "CVX",
            "COCA-COLA": "KO",
            "COCA COLA": "KO",
            "PEPSICO": "PEP",
            "MCDONALDS": "MCD",
            "VERIZON": "VZ",
            "AT&T": "T",
            "ATT": "T",
            "PFIZER": "PFE",
            "MERCK": "MRK"
            # Add more common company names and their primary ticker
        }

        query_upper = request.query.upper()
        extracted_symbols = set()

        # Attempt to match known company names
        for name, symbol in COMPANY_NAME_TO_SYMBOL_MAP.items():
            if name in query_upper:
                extracted_symbols.add(symbol)

        # Also look for direct ticker-like patterns (e.g., AAPL, TSM)
        # This regex finds words that are all uppercase, 1-5 characters long.
        potential_direct_tickers = re.findall(r'\b([A-Z]{1,5})\b', request.query) # Use original query for case-sensitive tickers if preferred
        for ticker in potential_direct_tickers:
            extracted_symbols.add(ticker)
        
        symbols_to_fetch = list(extracted_symbols)
        
        logger.info(f"Orchestrator: Symbols to fetch from API agent: {symbols_to_fetch}") # Changed from print
        # --- End symbol extraction ---

        api_tasks_with_timing_info = []
        if not symbols_to_fetch:
            logger.info("Orchestrator: No symbols identified in query to fetch market data.") # Changed from print
        else:
            for symbol in symbols_to_fetch:
                # Store start time with task or log around individual awaits if not using gather for these
                api_tasks_with_timing_info.append(
                    (symbol, time.time(), call_agent(client, "GET", f"{API_AGENT_URL}/stock/{symbol}"))
                )
>>>>>>> Stashed changes

        # Run API and Retriever tasks concurrently
        initial_results = await asyncio.gather(retrieval_task, *api_tasks, return_exceptions=True)

        # Process initial results and handle potential errors
        retrieved_data = None
        market_data_results = {}
        valid_market_data_for_analysis = {} # Store only successful results for analysis

<<<<<<< Updated upstream
        # Check retrieval result
        if isinstance(initial_results[0], Exception):
            print(f"Retriever agent call failed: {initial_results[0]}")
=======
        # Process retrieval result (first item in initial_results_gathered)
        retrieval_result = initial_results_gathered[0]
        # Log actual duration for retriever call now that it has completed
        log_duration(f"Orchestrator_Call_Retriever_Agent_Completed", retrieval_call_start_time)
        if isinstance(retrieval_result, Exception):
            logger.error(f"Retriever agent call failed: {retrieval_result}", exc_info=True) # Changed from print
            log_duration("Orchestrator_Total_Processing_Error_Retriever", orchestrator_total_start_time)
>>>>>>> Stashed changes
            raise HTTPException(status_code=500, detail="Failed to retrieve context.")
        else:
            # Ensure 'results' key exists, default to empty list
            retrieved_data = initial_results[0].get('results', []) if isinstance(initial_results[0], dict) else []

        # Check API agent results
        for i, symbol in enumerate(symbols_to_fetch):
            result = initial_results[i+1]
            if isinstance(result, Exception):
                logger.error(f"API agent call failed for {symbol}: {result}", exc_info=True) # Changed from print
                market_data_results[symbol] = {"error": f"Failed to fetch data for {symbol}"}
<<<<<<< Updated upstream
            elif isinstance(result, dict): # Check if result is a dict (successful fetch)
                 market_data_results[symbol] = result
                 valid_market_data_for_analysis[symbol] = result # Add successful fetches for analysis
            else:
                 # Handle unexpected result type
                 print(f"API agent call for {symbol} returned unexpected type: {type(result)}")
=======
            elif isinstance(result, dict):
                 market_data_results[symbol] = result 
                 api_response_info_field = result.get("info")

                 if symbol and isinstance(api_response_info_field, dict):
                     valid_market_data_for_analysis[symbol] = {
                         "symbol": symbol, # Use the loop variable 'symbol'
                         "info": api_response_info_field
                     }
                 else:
                     logger.warning(f"API result for {symbol} is missing 'info', or symbol is invalid. Skipping for analysis.") # Changed from print
            else:
                 logger.error(f"API agent call for {symbol} returned unexpected type: {type(result)}") # Changed from print
>>>>>>> Stashed changes
                 market_data_results[symbol] = {"error": "Unexpected response type from API agent"}

        # 3. Call Analysis Agent (if we have valid market data)
        analysis_results = {"error": "No valid market data for analysis"} # Default
        if valid_market_data_for_analysis:
             analysis_payload = {
                 "market_data": valid_market_data_for_analysis,
                 # Add portfolio AUM or holdings here if needed by analysis agent
                 "total_aum": 1_000_000 # Using default from analysis agent for now
             }
<<<<<<< Updated upstream
=======
             logger.debug(f"Orchestrator: Payload to Analysis Agent: {analysis_payload}") # Replaced detailed print block
             analysis_call_start_time = time.time()
>>>>>>> Stashed changes
             try:
                 analysis_response = await call_agent(client, "POST", f"{ANALYSIS_AGENT_URL}/analyze", json=analysis_payload)
                 analysis_results = analysis_response # Store the full analysis result
             except HTTPException as e:
<<<<<<< Updated upstream
                  # Handle analysis agent failure - log and continue, maybe return partial results
                  print(f"Analysis agent call failed: {e.detail}")
                  analysis_results = {"error": f"Analysis agent failed: {e.detail}"}
             except Exception as e:
                  print(f"Unexpected error calling analysis agent: {e}")
=======
                  log_duration("Orchestrator_Call_Analysis_Agent_Error", analysis_call_start_time)
                  logger.error(f"Analysis agent call failed: {e.detail}", exc_info=True) # Changed from print
                  analysis_results = {"error": f"Analysis agent failed: {e.detail}"}
             except Exception as e:
                  log_duration("Orchestrator_Call_Analysis_Agent_Error", analysis_call_start_time)
                  logger.error(f"Unexpected error calling analysis agent: {e}", exc_info=True) # Changed from print
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
             print(f"Language agent call failed: {e.detail}")
             final_narrative = f"Error: Language agent failed: {e.detail}"
        except Exception as e:
             print(f"Unexpected error calling language agent: {e}")
=======
             log_duration("Orchestrator_Call_Language_Agent_Error", language_call_start_time)
             logger.error(f"Language agent call failed: {e.detail}", exc_info=True) # Changed from print
             final_narrative = f"Error: Language agent failed: {e.detail}"
        except Exception as e:
             log_duration("Orchestrator_Call_Language_Agent_Error", language_call_start_time)
             logger.error(f"Unexpected error calling language agent: {e}", exc_info=True) # Changed from print
>>>>>>> Stashed changes
             final_narrative = f"Error: Unexpected error during language agent call: {e}"

    # Combine all results for the final response
    return OrchestratorResponse(
        retrieved_context=retrieved_data,
        market_data=market_data_results,
        analysis_results=analysis_results,
        final_narrative=final_narrative
    )

# Removed if __name__ == "__main__" block for deployment
# if __name__ == "__main__":
#     import uvicorn
#     # logger.info("Running Orchestrator Service. Access docs at http://localhost:8000/docs") # Changed from print
#     uvicorn.run(app, host="0.0.0.0", port=8000)