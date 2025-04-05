import json
import os
from logging_setup import logger_main

async def load_symbol_cache(filename):
    """Loads the symbol cache from a file."""
    try:
        if not os.path.exists(filename):
            return {'timestamp': 0, 'symbols': set()}

        with open(filename, 'r') as f:
            cache_data = json.load(f)
        cache_data['symbols'] = set(cache_data['symbols'])  # Convert list to set
        return cache_data
    except Exception as e:
        logger_main.error(f"Error loading symbol cache from {filename}: {e}")
        return {'timestamp': 0, 'symbols': set()}

async def save_symbol_cache(filename, cache_data):
    """Saves the symbol cache to a file."""
    try:
        with open(filename, 'w') as f:
            # Convert set to list for JSON serialization
            cache_data['symbols'] = list(cache_data['symbols'])
            json.dump(cache_data, f)
    except Exception as e:
        logger_main.error(f"Error saving symbol cache to {filename}: {e}")
