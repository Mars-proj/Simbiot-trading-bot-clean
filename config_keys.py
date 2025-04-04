# config_keys.py
from logging_setup import logger_main
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Supported exchanges
SUPPORTED_EXCHANGES = ['mexc', 'binance', 'bybit']  # Список поддерживаемых бирж

# API keys for users (loaded from .env)
API_KEYS = {
    "user1": {
        "mexc": {
            "api_key": os.getenv("USER1_MEXC_API_KEY", "your_mexc_api_key_for_user1"),
            "api_secret": os.getenv("USER1_MEXC_API_SECRET", "your_mexc_api_secret_for_user1")
        }
    },
    "user2": {
        "mexc": {
            "api_key": os.getenv("USER2_MEXC_API_KEY", "your_mexc_api_key_for_user2"),
            "api_secret": os.getenv("USER2_MEXC_API_SECRET", "your_mexc_api_secret_for_user2")
        }
    },
    "user3": {
        "mexc": {
            "api_key": os.getenv("USER3_MEXC_API_KEY", "your_mexc_api_key_for_user3"),
            "api_secret": os.getenv("USER3_MEXC_API_SECRET", "your_mexc_api_secret_for_user3")
        }
    }
}

def validate_api_keys(api_key, api_secret):
    """
    Validates API keys.
    Args:
        api_key (str): API key
        api_secret (str): API secret
    Returns:
        bool: True if keys are valid, False otherwise
    """
    if not api_key or not api_secret:
        logger_main.error("API key or secret is empty")
        return False
    if not isinstance(api_key, str) or not isinstance(api_secret, str):
        logger_main.error("API key or secret is not a string")
        return False
    # Additional validation can be added here (e.g., length checks)
    logger_main.info("API keys validated successfully")
    return True

# Validate API keys at startup
for user_id, exchanges in API_KEYS.items():
    for exchange_id, keys in exchanges.items():
        if not validate_api_keys(keys.get("api_key"), keys.get("api_secret")):
            logger_main.error(f"Invalid API keys for user {user_id} on {exchange_id}")
