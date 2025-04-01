import json
import asyncio
from logging_setup import logger_main
from redis_client import RedisClient

class CacheUtils:
    def __init__(self):
        self.redis = RedisClient()
        self.cache_ttl = 86400  # 24 hours TTL

    async def cache_symbol_data(self, symbol, data):
        """Caches symbol data in Redis."""
        try:
            key = f"symbol_data:{symbol}"
            await self.redis.setex(key, self.cache_ttl, json.dumps(data))
            logger_main.info(f"Cached symbol data for {symbol}")
            return True
        except Exception as e:
            logger_main.error(f"Error caching symbol data for {symbol}: {e}")
            return False

    async def get_symbol_data(self, symbol):
        """Retrieves symbol data from Redis."""
        try:
            key = f"symbol_data:{symbol}"
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger_main.error(f"Error retrieving symbol data for {symbol}: {e}")
            return None

    async def cache_invalid_symbol(self, exchange_id, symbol):
        """Caches an invalid symbol in Redis."""
        try:
            key = f"invalid_symbols:{exchange_id}"
            invalid_symbols = await self.get_invalid_symbols(exchange_id) or set()
            invalid_symbols.add(symbol)
            await self.redis.setex(key, self.cache_ttl, json.dumps(list(invalid_symbols)))
            logger_main.info(f"Cached invalid symbol {symbol} for {exchange_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error caching invalid symbol {symbol} for {exchange_id}: {e}")
            return False

    async def get_invalid_symbols(self, exchange_id):
        """Retrieves invalid symbols from Redis."""
        try:
            key = f"invalid_symbols:{exchange_id}"
            data = await self.redis.get(key)
            if data:
                return set(json.loads(data))
            return None
        except Exception as e:
            logger_main.error(f"Error retrieving invalid symbols for {exchange_id}: {e}")
            return None

__all__ = ['CacheUtils']
