import ccxt.async_support as ccxt
from utils import logger_main, log_exception

async def create_exchange(preferred_exchange, exchange_data, loop=None):
    """Creates an exchange object with the specified parameters"""
    try:
        exchange = getattr(ccxt, preferred_exchange)({
            'apiKey': exchange_data['api_key'],
            'secret': exchange_data['api_secret'],
            'enableRateLimit': exchange_data.get('enableRateLimit', True),
            'adjustForTimeDifference': True,
            'recvWindow': 20000,
            'defaultType': 'spot',
        })
        exchange.set_sandbox_mode(False)
        api_url = exchange.urls.get('api', {}).get('public', 'Unknown endpoint')
        test_url = exchange.urls.get('test', {}).get('public', 'Unknown test endpoint')
        logger_main.debug(f"API endpoint for {preferred_exchange}: {api_url}")
        logger_main.debug(f"Test endpoint for {preferred_exchange}: {test_url}")
        if 'test' in api_url.lower() or 'sandbox' in api_url.lower():
            raise Exception(f"Detected test endpoint: {api_url}. Expected real endpoint.")
        return exchange
    except Exception as e:
        logger_main.error(f"Error creating exchange object for {preferred_exchange}: {str(e)}")
        log_exception(f"Error creating exchange object: {str(e)}", e)
        return None

__all__ = ['create_exchange']
