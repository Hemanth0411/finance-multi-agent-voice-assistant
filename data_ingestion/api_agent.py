import yfinance as yf
import pandas as pd

def get_stock_data(symbol: str) -> dict | None:
    """Fetches stock data for a given symbol using yfinance.

    Args:
        symbol: The stock ticker symbol (e.g., 'TSM', '005930.KS').

    Returns:
        A dictionary containing 'price' (1-day history DataFrame) and 'info',
        or None if the symbol is invalid or data fetch fails.
    """
    try:
        stock = yf.Ticker(symbol)
        # Check if the ticker is valid by trying to access info
        if not stock.info:
            print(f"Warning: No info found for symbol {symbol}. It might be invalid.")
            return None

        hist = stock.history(period="1d")
        if hist.empty:
             print(f"Warning: No history found for symbol {symbol} for period '1d'.")
             # Still return info if available
             return {"price": pd.DataFrame(), "info": stock.info}

        # Convert Timestamps to strings for JSON serialization if needed later
        # hist.index = hist.index.strftime('%Y-%m-%d %H:%M:%S')

        return {
            "price": hist.to_dict('records'), # More JSON friendly
            "info": stock.info
        }
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

if __name__ == '__main__':
    # Example usage:
    tsm_data = get_stock_data("TSM")
    if tsm_data:
        print("\nTSM Data:")
        # print(f"Price History (1d):\n{tsm_data['price']}")
        print(f"Price History (1d): {len(tsm_data['price'])} records") # Print length instead of full dict
        print(f"Info: {tsm_data['info'].get('longName', 'N/A')}, Currency: {tsm_data['info'].get('currency', 'N/A')}")

    samsung_data = get_stock_data("005930.KS") # Samsung Electronics
    if samsung_data:
        print("\nSamsung Data:")
        # print(f"Price History (1d):\n{samsung_data['price']}")
        print(f"Price History (1d): {len(samsung_data['price'])} records")
        print(f"Info: {samsung_data['info'].get('longName', 'N/A')}, Currency: {samsung_data['info'].get('currency', 'N/A')}")

    invalid_data = get_stock_data("INVALIDTICKER")
    if not invalid_data:
        print("\nHandled invalid ticker correctly.") 