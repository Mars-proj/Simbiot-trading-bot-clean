import ccxt.async_support as ccxt
from logging_setup import logger_main
from config_keys import SUPPORTED_EXCHANGES, API_KEYS, validate_api_keys
import os

def create_exchange(exchange_id, user_id, testnet=False):
    """Creates an exchange instance with user-specific API keys and configurations."""
    try:
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return None

        # Get user API keys
        user_api_keys = API_KEYS.get(user_id, {}).get(exchange_id, {})
        api_key = user_api_keys.get("api_key")
        api_secret = user_api_keys.get("api_secret")

        if not validate_api_keys(api_key, api_secret):
            logger_main.error(f"Invalid API keys for user {user_id} on {exchange_id}")
            return None

        # Exchange configuration
        exchange_config = {
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'rateLimit': int(os.getenv("RATE_LIMIT", 2000)),  # Configurable rate limit
        }

        # Create exchange instance
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class(exchange_config)

        # Set testnet if specified
        if testnet:
            if hasattr(exchange, 'urls') and 'test' in exchange.urls:
                exchange.urls['api'] = exchange.urls['test']
                logger_main.info(f"Using testnet for {exchange_id}")
            else:
                logger_main.warning(f"Testnet not supported for {exchange_id}, using live mode")

        # Additional configuration for specific exchanges
        if exchange_id == 'mexc':
            exchange.options['defaultType'] = 'spot'
            exchange.options['rateLimit'] = 1000  # MEXC-specific rate limit

        # Store user_id and testnet status in the exchange object for later use
        exchange.user_id = user_id
        exchange.testnet = testnet

        logger_main.info(f"Created exchange instance for {exchange_id} (user: {user_id}, testnet: {testnet}) with rateLimit: {exchange.rateLimit}")
        return exchange
    except Exception as e:
        logger_main.error(f"Error creating exchange instance for {exchange_id}: {e}")
        return None

__all__ = ['create_exchange']
