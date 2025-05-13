import re
import json
from typing import Any, Dict, List
import hashlib
import os
from pathlib import Path
import logging
import time

def log_duration(operation_name: str, start_time: float):
    duration_ms = (time.time() - start_time) * 1000
    logger.info(f"PERF_METRIC: {operation_name} took {duration_ms:.2f} ms")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a cache directory
CACHE_DIR = Path(os.getenv("CACHE_DIR", "./temp_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# --- Data Cleaning Utilities ---

def remove_special_characters(text: str) -> str:
    """Removes common special characters, keeping alphanumeric and basic punctuation."""
    return re.sub(r'[^a-zA-Z0-9\s.,!?-]', '', text)

def normalize_whitespace(text: str) -> str:
    """Replaces multiple whitespace characters with a single space and trims."""
    return re.sub(r'\s+', ' ', text).strip()

def clean_text_data(text: str) -> str:
    """Applies a series of cleaning steps to raw text."""
    if not isinstance(text, str):
        logger.warning(f"Expected string for cleaning, got {type(text)}. Returning as is.")
        return str(text) # Or handle more gracefully
    text = remove_special_characters(text)
    text = normalize_whitespace(text)
    # Add more cleaning steps as needed (e.g., lowercasing, HTML tag removal if not done prior)
    return text

def clean_financial_number(value: Any) -> float | None:
    """
    Cleans and converts a value that might represent a financial number 
    (e.g., "1,234.56M", "$500K", "(50.2B)") into a float.
    Handles K, M, B suffixes for thousands, millions, billions.
    Handles numbers in parentheses as negative.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    text = value.strip().upper()
    
    is_negative = False
    if text.startswith('(') and text.endswith(')'):
        is_negative = True
        text = text[1:-1]

    text = text.replace('$', '').replace(',', '')
    
    multiplier = 1.0
    if text.endswith('K'):
        multiplier = 1_000
        text = text[:-1]
    elif text.endswith('M'):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith('B'):
        multiplier = 1_000_000_000
        text = text[:-1]

    try:
        number = float(text) * multiplier
        return -number if is_negative else number
    except ValueError:
        logger.warning(f"Could not convert '{value}' to a financial number.")
        return None

# --- Caching Utilities ---

def generate_cache_key(*args: Any, **kwargs: Any) -> str:
    """Generates a simple hash key based on function arguments for caching."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    key_string = "_".join(key_parts)
    return hashlib.md5(key_string.encode('utf-8')).hexdigest()

def save_to_cache(key: str, data: Any, cache_dir: Path = CACHE_DIR) -> None:
    """Saves data to a JSON file in the cache directory."""
    cache_file = cache_dir / f"{key}.json"
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f)
        logger.debug(f"Saved data to cache: {cache_file}")
    except IOError as e:
        logger.error(f"Error saving data to cache file {cache_file}: {e}")
    except TypeError as e:
        logger.error(f"Error serializing data for caching (key: {key}): {e}")

def load_from_cache(key: str, cache_dir: Path = CACHE_DIR) -> Any | None:
    """Loads data from a JSON file in the cache directory if it exists."""
    cache_file = cache_dir / f"{key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            logger.debug(f"Loaded data from cache: {cache_file}")
            return data
        except IOError as e:
            logger.error(f"Error loading data from cache file {cache_file}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from cache file {cache_file}: {e}")
            # Optionally, delete corrupted cache file
            # cache_file.unlink(missing_ok=True)
    return None


# Removed if __name__ == "__main__" block for deployment
# if __name__ == "__main__":
#     # Example usage of cleaning functions
#     raw_text = "  Hello   World!  This is a test with 123, ABC and some $#@ special chars.  "
#     cleaned = clean_text_data(raw_text)
#     logger.info(f"Original: '{raw_text}'")
#     logger.info(f"Cleaned:  '{cleaned}'")
# 
#     num1 = clean_financial_number("1,250.75M")
#     logger.info(f"Cleaned '1,250.75M': {num1}")
#     num2 = clean_financial_number("$(2.5B)")
#     logger.info(f"Cleaned '$(2.5B)': {num2}")
#     num3 = clean_financial_number("300K")
#     logger.info(f"Cleaned '300K': {num3}")
#     num4 = clean_financial_number("InvalidData")
#     logger.info(f"Cleaned 'InvalidData': {num4}")
# 
#     # Example usage of caching functions
#     data_to_cache = {"name": "John Doe", "value": 42, "items": [1, 2, 3]}
#     params = ("user_data", 123)
#     cache_k = generate_cache_key(*params, filter="active")
# 
#     # Save to cache
#     save_to_cache(cache_k, data_to_cache)
#     logger.info(f"Saved data with cache key: {cache_k}")
# 
#     # Load from cache
#     loaded_data = load_from_cache(cache_k)
#     if loaded_data:
#         logger.info(f"Loaded data from cache: {loaded_data}")
#         assert loaded_data == data_to_cache
#     else:
#         logger.info("Cache miss or error loading.")
# 
#     # Test with a new key (cache miss)
#     missing_data = load_from_cache("non_existent_key")
#     assert missing_data is None
#     logger.info("Tested cache miss for 'non_existent_key'.")
# 
#     logger.info("Data utils module loaded and example functions executed.") 