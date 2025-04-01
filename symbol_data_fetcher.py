from logging_setup import logger_main
from exchange_factory import create_exchange
from symbol_handler import validate_symbol
from cache_utils import CacheUtils

async def fetch_symbol_data(exchange_id, user_id, symbol, testnet=False):
    """Fetches symbol data with caching support."""
    try:
        # Validate symbol
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None

        # Check cache first
        cache = CacheUtils()
        cached_data = await cache.get_symbol_data(symbol)
        if cached_data:
            return cached_data

        # Fetch symbol data from exchange
        symbol_info = await exchange.fetch_ticker(symbol)
        if not symbol_info:
            logger_main.error(f"Failed to fetch symbol data for {symbol} on {exchange_id}")
            return None

        # Extract relevant data
        data = {
            'symbol': symbol,
            'price': symbol_info.get('last', 0),
            'volume': symbol_info.get('baseVolume', 0),
            'bid': symbol_info.get('bid', 0),
            'ask': symbol_info.get('ask', 0),
            'timestamp': symbol_info.get('timestamp', 0)
        }

        # Cache the data
        await cache.cache_symbol_data(symbol, data)

        logger_main.info(f"Fetched symbol data for {symbol} on {exchange_id}: {data}")
        return data
    except Exception as e:
        logger_main.error(f"Error fetching symbol data for {symbol} on {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['fetch_symbol_data']
