import json
import os
from logging_setup import logger_main

async def load_symbol_cache(filename):
    """Loads the symbol cache from a file."""
    try:
        if not os.path.exists(filename):
            logger_main.warning(f"Cache file {filename} does not exist, returning default")
            return {'timestamp': 0, 'symbols': set()}

        logger_main.debug(f"Attempting to load cache file {filename}")
        with open(filename, 'r') as f:
            cache_data = json.load(f)
        logger_main.debug(f"Loaded cache data: {cache_data}")
        
        if 'timestamp' not in cache_data or 'symbols' not in cache_data:
            logger_main.error(f"Invalid cache format in {filename}: missing 'timestamp' or 'symbols'")
            return {'timestamp': 0, 'symbols': set()}

        cache_data['symbols'] = set(cache_data['symbols'])  # Convert list to set
        logger_main.debug(f"Converted symbols to set: {len(cache_data['symbols'])} symbols")
        return cache_data
    except Exception as e:
        logger_main.error(f"Error loading symbol cache from {filename}: {e}")
        return {'timestamp': 0, 'symbols': set()}

async def save_symbol_cache(filename, cache_data):
    """Saves the symbol cache to a file."""
    try:
        logger_main.debug(f"Saving cache to {filename}: {cache_data}")
        with open(filename, 'w') as f:
            # Convert set to list for JSON serialization
            cache_data['symbols'] = list(cache_data['symbols'])
            json.dump(cache_data, f)
        logger_main.debug(f"Successfully saved cache to {filename}")
    except Exception as e:
        logger_main.error(f"Error saving symbol cache to {filename}: {e}")
