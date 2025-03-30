from logging_setup import logger_main
from redis_client import redis_client

async def cache_symbol_data(symbol: str, data: dict, ttl: int = 3600) -> bool:
    """Caches symbol data in Redis if the symbol is not problematic."""
    try:
        # Check if the symbol is problematic (e.g., low volume)
        volume = data.get('volume', 0)
        if volume < 1000:  # Arbitrary threshold for low volume
            logger_main.warning(f"Symbol {symbol} has low volume ({volume}), not caching")
            return False

        key = f"symbol_data:{symbol}"
        await redis_client.set(key, data, ex=ttl)
        logger_main.info(f"Cached data for symbol {symbol} with TTL {ttl}")
        return True
    except Exception as e:
        logger_main.error(f"Error caching data for symbol {symbol}: {e}")
        return False

async def get_symbol_data(symbol: str) -> dict:
    """Fetches symbol data from Redis."""
    try:
        key = f"symbol_data:{symbol}"
        data = await redis_client.get(key)
        if data is None:
            logger_main.info(f"No cached data for symbol {symbol}")
            return None
        logger_main.info(f"Fetched cached data for symbol {symbol}")
        return data
    except Exception as e:
        logger_main.error(f"Error fetching cached data for symbol {symbol}: {e}")
        return None

__all__ = ['cache_symbol_data', 'get_symbol_data']
