import ccxt.async_support as ccxt
from logging_setup import logger_main
from config_keys import API_KEYS, validate_api_keys

async def create_exchange(exchange_id, user_id, testnet=False, rate_limit=500, enable_rate_limit=True, enable_rate_limit_monitoring=False):
    """Creates an exchange instance for the specified user with configurable settings."""
    try:
        if user_id not in API_KEYS or exchange_id not in API_KEYS[user_id]:
            logger_main.error(f"No API keys found for user {user_id} on {exchange_id}")
            return None

        api_key = API_KEYS[user_id][exchange_id]["api_key"]
        api_secret = API_KEYS[user_id][exchange_id]["api_secret"]
        if not validate_api_keys(api_key, api_secret):
            logger_main.error(f"Invalid API keys for user {user_id} on {exchange_id}")
            return None

        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': enable_rate_limit,
            'rateLimit': rate_limit,
        })

        if testnet:
            try:
                exchange.set_sandbox_mode(True)
                logger_main.info(f"Enabled sandbox mode for {exchange_id}")
            except Exception as e:
                logger_main.warning(f"Exchange {exchange_id} does not support sandbox mode: {e}")
                return None

        # Rate limit monitoring
        if enable_rate_limit_monitoring:
            exchange.options['warnOnFetchRateLimit'] = True
            logger_main.info(f"Enabled rate limit monitoring for {exchange_id}")

        logger_main.info(f"Created exchange instance for {exchange_id} (user: {user_id}) with settings: rateLimit={rate_limit}, enableRateLimit={enable_rate_limit}")
        return exchange
    except Exception as e:
        logger_main.error(f"Error creating exchange instance for {exchange_id} (user: {user_id}): {e}")
        return None

__all__ = ['create_exchange']
