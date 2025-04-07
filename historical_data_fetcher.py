# historical_data_fetcher.py
import logging
import redis.asyncio as redis
import json

logger = logging.getLogger("main")

async def get_redis_client():
    """Инициализация Redis клиента."""
    return await redis.from_url("redis://localhost:6379/0")

async def fetch_historical_data(symbol, exchange, since, limit, timeframe, user):
    redis_client = await get_redis_client()
    try:
        # Формируем ключ для кэширования
        cache_key = f"ohlcv:{symbol}:{timeframe}:{since}:{limit}"
        # Проверяем, есть ли данные в кэше
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            logger.debug(f"Retrieved {symbol} OHLCV data from cache")
            return json.loads(cached_data.decode())

        # Если данных нет в кэше, запрашиваем их
        logger.debug(f"Fetching OHLCV data for {symbol} with timeframe {timeframe}, since={since}, limit={limit}")
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since, limit)
        logger.debug(f"Fetched {len(ohlcv)} OHLCV data points for {symbol}")

        # Сохраняем данные в кэш с TTL 24 часа
        await redis_client.set(cache_key, json.dumps(ohlcv), ex=86400)
        logger.debug(f"Cached {symbol} OHLCV data in Redis")
        return ohlcv
    except Exception as e:
        logger.error(f"Failed to fetch OHLCV data for {symbol}: {type(e).__name__}: {str(e)}")
        raise
    finally:
        await redis_client.close()
