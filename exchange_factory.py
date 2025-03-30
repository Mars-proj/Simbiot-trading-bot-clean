import ccxt.async_support as ccxt
from logging_setup import logger_main
from config_keys import API_KEYS, SUPPORTED_EXCHANGES, validate_api_keys
from bot_user_data import user_data

def create_exchange(exchange_id, user_id=None, testnet=False, **kwargs):
    """Creates an exchange instance for a user (with API keys) or for public requests (without API keys)."""
    try:
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return None

        # Base configuration
        config = {
            'enableRateLimit': True,
            **kwargs  # Additional parameters
        }

        # Add optional configuration parameters
        if 'timeout' in kwargs:
            config['timeout'] = kwargs['timeout']
        if 'rate_limit' in kwargs:
            config['rateLimit'] = kwargs['rate_limit']
        if 'defaultTimeInForce' in kwargs:
            config['defaultTimeInForce'] = kwargs['defaultTimeInForce']

        if user_id:
            # Create exchange with API keys
            if user_id not in user_data:
                logger_main.error(f"User {user_id} not found in user_data")
                return None

            api_key = API_KEYS.get(user_id, {}).get(exchange_id, {}).get("api_key")
            api_secret = API_KEYS.get(user_id, {}).get(exchange_id, {}).get("api_secret")
            if not validate_api_keys(api_key, api_secret):
                logger_main.error(f"API keys for {exchange_id} failed validation for user {user_id}")
                return None

            config.update({
                'apiKey': api_key,
                'secret': api_secret,
            })
            log_message = f"Exchange instance {exchange_id} (CCXT v.{ccxt.__version__}) created for user {user_id}"
        else:
            # Create exchange for public requests
            log_message = f"Exchange {exchange_id} (CCXT v.{ccxt.__version__}) configured for public requests"

        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class(config)

        # Additional user-specific setup
        if user_id:
            if 'enable_futures' in kwargs and kwargs['enable_futures']:
                exchange.options['defaultType'] = 'future'
                log_message += " with futures enabled"
            if 'enable_margin' in kwargs and kwargs['enable_margin']:
                exchange.options['defaultType'] = 'margin'
                log_message += " with margin enabled"

        # Enable testnet if specified
        if testnet:
            exchange.set_sandbox_mode(True)
            log_message += " in testnet mode"

        # Add rate limit monitoring for MEXC
        if exchange_id == 'mexc':
            exchange.rate_limit_monitor = {
                'requests': 0,
                'limit': 1200,  # MEXC API limit per minute (example)
                'window': 60,  # 60 seconds
                'start_time': 0
            }
            logger_main.info(f"Enabled rate limit monitoring for MEXC: {exchange.rate_limit_monitor}")

        # Log the full configuration
        logger_main.info(f"{log_message} with config: {config}")
        return exchange
    except Exception as e:
        logger_main.error(f"Error creating exchange instance {exchange_id}" + (f" for {user_id}" if user_id else "") + f": {e}")
        return None

__all__ = ['create_exchange']
