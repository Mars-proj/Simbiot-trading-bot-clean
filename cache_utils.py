from logging_setup import logger_main
from redis_client import redis_client

async def cache_symbol_data(symbol, data, min_volume=1000, cache_ttl=3600):
    """Caches symbol data in Redis with configurable volume threshold and TTL."""
    try:
        # Check if symbol is problematic (e.g., low volume)
        if 'volume' in data and data['volume'] < min_volume:
            logger_main.warning(f"Symbol {symbol} has low volume ({data['volume']}), below threshold {min_volume}, not caching")
            return False
        key = f"symbol_data:{symbol}"
        await redis_client.set(key, data, ex=cache_ttl)
        logger_main.info(f"Cached data for symbol {symbol} for {cache_ttl} seconds")
        return True
    except Exception as e:
        logger_main.error(f"Error caching data for symbol {symbol}: {e}")
        return False

async def get_cached_symbol_data(symbol):
    """Gets cached symbol data from Redis."""
    try:
        key = f"symbol_data:{symbol}"
        data = await redis_client.get(key)
        if data:
            logger_main.info(f"Retrieved cached data for symbol {symbol}")
            return data
        return None
    except Exception as e:
        logger_main.error(f"Error retrieving cached data for symbol {symbol}: {e}")
        return None

__all__ = ['cache_symbol_data', 'get_cached_symbol_data']
