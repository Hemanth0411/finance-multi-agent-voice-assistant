import yfinance as yf
import pandas as pd
import time
import logging
from .data_utils import log_duration # Assuming data_utils is in the same directory or accessible

logger = logging.getLogger(__name__)

def get_stock_data(symbol: str) -> dict | None:
    """Fetches stock data for a given symbol using yfinance.

    Args:
        symbol: The stock ticker symbol (e.g., 'TSM', '005930.KS').

    Returns:
        A dictionary containing 'price' (1-day history DataFrame) and 'info',
        or None if the symbol is invalid or data fetch fails.
    """
    yf_call_start_time = time.time()
    try:
        stock = yf.Ticker(symbol)
        info_data = stock.info
        log_duration(f"API_YFinance_Info_{symbol}", yf_call_start_time)
        
        if not info_data or not info_data.get('symbol'):
            logger.warning(f"No comprehensive info found for symbol {symbol}. It might be invalid or delisted.")
            return None

        hist_fetch_start_time = time.time()
        hist = stock.history(period="1d")
        log_duration(f"API_YFinance_History_{symbol}", hist_fetch_start_time)

        if hist.empty:
             logger.warning(f"No 1-day history found for symbol {symbol}. Returning info only.")
             return {"price": [], "info": info_data}

        return {
            "price": hist.to_dict('records'),
            "info": info_data
        }
    except Exception as e:
        logger.error(f"Error fetching data for {symbol} using yfinance: {e}", exc_info=True)
        return None

# Removed if __name__ == '__main__' block for deployment 