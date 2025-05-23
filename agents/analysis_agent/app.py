from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

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
    try:
        # Validate market_data structure before passing to calculation
        valid_market_data = {}
        if request.market_data:
            for symbol, data_dict in request.market_data.items():
                 try:
                      # Attempt to parse into StockInfo to ensure structure
                      stock_info_obj = StockInfo(symbol=symbol, info=data_dict.get('info', {})) # Get info dict
                      valid_market_data[symbol] = stock_info_obj
                 except Exception as pydantic_error:
                      print(f"Warning: Skipping symbol {symbol} due to invalid data format: {pydantic_error}")


        # Calculate Asia tech exposure using the improved logic
        asia_exposure_percent = calculate_exposure(valid_market_data, request.total_aum, region="Asia")

        # Placeholder for earnings analysis - this would likely involve the retrieved context
        # earnings_summary = analyze_earnings(retrieved_context)

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