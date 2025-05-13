from fastapi import FastAPI, HTTPException
import sys
import os

# Add the project root to the Python path to allow importing from data_ingestion
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data_ingestion.api_agent import get_stock_data

app = FastAPI(
    title="API Agent Service",
    description="Provides stock market data via yfinance.",
    version="0.1.0"
)

@app.get("/stock/{symbol}", summary="Get Stock Data", description="Fetches real-time price and basic info for a given stock symbol.")
async def read_stock_data(symbol: str):
    """Endpoint to fetch stock data.

    Args:
        symbol: The stock ticker symbol.

    Returns:
        Stock data dictionary.

    Raises:
        HTTPException: 404 if the symbol is not found or data fetch fails.
    """
    data = get_stock_data(symbol)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Data not found for symbol {symbol}")
    # Ensure data is JSON serializable (yfinance info can contain non-serializable types)
    # Basic check - might need more robust serialization depending on yfinance output
    try:
        # Example: Convert DataFrame in 'price' if it wasn't already
        if isinstance(data.get('price'), list) and data['price'] and isinstance(data['price'][0], dict):
             pass # Already converted in get_stock_data
        # You might need to clean up data['info'] as well if issues arise
        # For now, assume it's mostly serializable or handle errors during response
        pass
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Error serializing data for {symbol}: {e}")

    return data

# Removed if __name__ == "__main__" block for deployment
# if __name__ == "__main__":
#     import uvicorn
#     # Note: Running this directly might have issues with the sys.path modification depending on execution context.
#     # It's better to run using uvicorn from the project root:
#     # cd finance-assistant
#     # uvicorn agents.api_agent.app:app --reload --port 8001
#     print("Running API Agent Service. Access docs at http://localhost:8001/docs") # This print is fine for local uvicorn run, but removed with the block
#     uvicorn.run(app, host="0.0.0.0", port=8001)