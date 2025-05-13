import sys # Moved to top
import os # Moved to top

# Add project root to sys.path to allow finding data_ingestion
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from data_ingestion.data_utils import log_duration
import time # Add time import

app = FastAPI(
    title="Analysis Agent Service",
    description="Performs financial analysis like risk exposure calculation.",
    version="0.1.0"
)

# Pydantic models for input data structure validation
class StockInfo(BaseModel):
    symbol: str
    info: Dict[str, Any] # From yfinance
    # Add other relevant fields as needed, e.g., region, sector
    # For now, we'll mock region based on symbol

class PortfolioAnalysisRequest(BaseModel):
    market_data: Dict[str, StockInfo] # Symbol -> StockInfo
    # Add portfolio holdings info here later if needed for AUM calculation
    # e.g., portfolio_holdings: Dict[str, float] # Symbol -> Value or Quantity
    total_aum: float = 1_000_000 # Dummy AUM for percentage calculation

class AnalysisResponse(BaseModel):
    risk_metrics: Dict[str, Any]
    # earnings_summary: Dict[str, str]

def get_region_mock(symbol: str) -> str:
    """Mock function to assign region based on symbol."""
    if symbol == "TSM":
        return "Asia"
    elif symbol == "005930.KS":
        return "Asia"
    # Add more mappings or use actual data source if available
    return "Other"

def calculate_exposure(market_data: Dict[str, StockInfo], total_aum: float, region: str = "Asia") -> float | None:
    """Calculates portfolio exposure to a region based on market cap of provided stocks.

       Assumes market_data represents the relevant portfolio slice for the query.
       Uses marketCap from yfinance info if available.
    """
    asia_tech_value = 0.0
    total_value_in_data = 0.0

    if not market_data:
        return 0.0

    for symbol, data in market_data.items():
        stock_value = 0
        # Ensure data and info exist and info is a dict before accessing
        if data and data.info and isinstance(data.info, dict):
             stock_value = data.info.get('marketCap')
             # Use previousClose as fallback if marketCap is missing/zero, assuming it reflects some value
             if not stock_value or stock_value <= 0:
                  stock_value = data.info.get('previousClose', 0)
             # Ensure stock_value is a number, default to 0 if not
             if not isinstance(stock_value, (int, float)):
                  stock_value = 0
        else:
             print(f"Warning: Missing or invalid info for symbol {symbol}")
             stock_value = 0 # Assign zero value if info is missing

        total_value_in_data += stock_value

        # Check if it's an Asia Tech stock
        stock_region = get_region_mock(symbol)
        stock_sector = data.info.get('sector', '').lower() if data and data.info and isinstance(data.info, dict) else ''

        if stock_region == region and stock_sector == 'technology':
            asia_tech_value += stock_value

    if total_value_in_data <= 0:
        # Avoid division by zero, return 0% if no value found in provided data
        return 0.0

    # Calculate exposure percentage based *only* on the market data provided
    exposure_percent = (asia_tech_value / total_value_in_data) * 100
    return round(exposure_percent, 2)

@app.post("/analyze", response_model=AnalysisResponse, summary="Analyze Portfolio Data", description="Calculates risk metrics like regional exposure based on provided market data.")
async def analyze_portfolio(request: PortfolioAnalysisRequest):
    """Endpoint to perform analysis.

    Args:
        request: PortfolioAnalysisRequest containing market data.

    Returns:
        AnalysisResponse containing calculated metrics.

    Raises:
        HTTPException: 500 if analysis fails.
    """
    analysis_start_time = time.time() # Start timer
    try:
        # The request.market_data should already contain StockInfo objects if the Orchestrator is correct.
        # We can directly use it if the Pydantic validation for PortfolioAnalysisRequest passed.
        
        # Filter for valid StockInfo objects, though Pydantic should ensure this for PortfolioAnalysisRequest
        # This is more of a sanity check or if we were to change how data is passed.
        valid_market_data_for_calc = {}
        if request.market_data:
            for symbol, stock_info_obj in request.market_data.items():
                if isinstance(stock_info_obj, StockInfo) and stock_info_obj.info is not None:
                    valid_market_data_for_calc[symbol] = stock_info_obj
                else:
                    print(f"Warning: Skipping symbol {symbol} in Analysis Agent because it was not a valid StockInfo object or info was None.")

        # Calculate Asia tech exposure using the improved logic
        asia_exposure_percent = calculate_exposure(valid_market_data_for_calc, request.total_aum, region="Asia")

        # Placeholder for earnings analysis - this would likely involve the retrieved context
        # earnings_summary = analyze_earnings(retrieved_context)

        log_duration("Analysis_Agent_Total_Request", analysis_start_time) # Log duration before returning
        return AnalysisResponse(
            risk_metrics={
                "asia_tech_exposure_percent": asia_exposure_percent
                # Add other metrics here
            }
            # earnings_summary=earnings_summary
        )
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

if __name__ == "__main__":
    import uvicorn
    # Run using:
    # cd finance-assistant
    # uvicorn agents.analysis_agent.app:app --reload --port 8003
    print("Running Analysis Agent Service. Access docs at http://localhost:8003/docs")
    uvicorn.run(app, host="0.0.0.0", port=8003) 