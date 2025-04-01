from logging_setup import logger_main

# API keys for users
API_KEYS = {
    "user1": {
        "mexc": {"api_key": "mx0vglGRsaFvzo2b0j", "api_secret": "794defd4ae1f47c08cefd4d1c0a4bd41"},
    },
    "user2": {
        "mexc": {"api_key": "mx0vgl99fkHYT0VQ27", "api_secret": "07b2e5086e334472ad35513b2dc45dd9"},
    }
}

# Preferred exchanges for users
PREFERRED_EXCHANGES = {
    "user1": "mexc",  # Use MEXC for real trading
    "user2": "mexc"
}

# Supported exchanges
SUPPORTED_EXCHANGES = ['mexc', 'binance', 'bybit', 'kucoin', 'okx']

# General settings
MAX_OPEN_TRADES = 10
MIN_TRADE_AMOUNT = 0.01
MAX_LEVERAGE = 5
MAX_POSITION_SIZE = 10000.0  # Maximum total position size in USDT
MAX_POSITION_SIZE_PER_SYMBOL = 5000.0  # Maximum position size per symbol in USDT

def validate_api_keys(api_key, api_secret):
    """Validates API keys with strict checks."""
    try:
        if not api_key or not api_secret:
            logger_main.error("API key or secret is empty")
            return False
        if len(api_key) < 10 or len(api_secret) < 10:  # Minimum length check
            logger_main.error("API key or secret is too short (minimum length: 10 characters)")
            return False
        if not api_key.isalnum() or not api_secret.isalnum():  # Alphanumeric check
            logger_main.error("API key or secret contains invalid characters (must be alphanumeric)")
            return False
        logger_main.info("API keys validated successfully")
        return True
    except Exception as e:
        logger_main.error(f"Error validating API keys: {e}")
        return False

__all__ = ['API_KEYS', 'PREFERRED_EXCHANGES', 'SUPPORTED_EXCHANGES', 'MAX_OPEN_TRADES', 'MIN_TRADE_AMOUNT', 'MAX_LEVERAGE', 'MAX_POSITION_SIZE', 'MAX_POSITION_SIZE_PER_SYMBOL', 'validate_api_keys']
