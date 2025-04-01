import os
import time
from logging_setup import logger_main
from redis_client import RedisClient

class CacheUtils:
    def __init__(self):
        self.redis = RedisClient()
        self.volume_threshold = float(os.getenv("CACHE_VOLUME_THRESHOLD", 1000))
        self.cache_ttl = int(os.getenv("CACHE_TTL", 3600))  # TTL in seconds (1 hour by default)

    async def cache_symbol_data(self, symbol, data):
        """Caches symbol data if volume threshold is met."""
        try:
            if not data or 'volume' not in data:
                logger_main.error(f"Invalid data for symbol {symbol}: missing volume")
                return False

            volume = data.get('volume', 0)
            if volume < self.volume_threshold:
                logger_main.warning(f"Symbol {symbol} volume {volume} below threshold {self.volume_threshold}, not caching")
                return False

            cache_key = f"symbol_data:{symbol}"
            await self.redis.setex(cache_key, self.cache_ttl, data)
            logger_main.info(f"Cached data for symbol {symbol} with TTL {self.cache_ttl} seconds")
            return True
        except Exception as e:
            logger_main.error(f"Error caching data for symbol {symbol}: {e}")
            return False

    async def get_symbol_data(self, symbol):
        """Retrieves cached symbol data."""
        try:
            cache_key = f"symbol_data:{symbol}"
            data = await self.redis.get(cache_key)
            if data:
                logger_main.info(f"Retrieved cached data for symbol {symbol}")
                return data
            return None
        except Exception as e:
            logger_main.error(f"Error retrieving cached data for symbol {symbol}: {e}")
            return None

    async def clear_expired_cache(self):
        """Clears expired cache entries."""
        try:
            keys = await self.redis.keys("symbol_data:*")
            current_time = int(time.time())
            expired_keys = []
            for key in keys:
                ttl = await self.redis.ttl(key)
                if ttl < 0:  # TTL < 0 means the key has expired
                    expired_keys.append(key)

            for key in expired_keys:
                await self.redis.delete(key)
                logger_main.info(f"Cleared expired cache for {key}")

            logger_main.info(f"Cleared {len(expired_keys)} expired cache entries")
            return True
        except Exception as e:
            logger_main.error(f"Error clearing expired cache: {e}")
            return False

__all__ = ['CacheUtils']
