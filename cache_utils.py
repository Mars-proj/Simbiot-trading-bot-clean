import asyncio
import json
import time
from redis_initializer import redis_client
from logging_setup import logger_main
from utils import log_exception

CACHE_TTL = 300
MAX_CACHE_SIZE = 10000

local_ticker_cache = {}
local_cache_timestamp = {}

async def clear_expired_cache():
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    try:
        keys = await redis_client.client.keys("ohlcv:*")
        current_time = time.time()
        for key in keys:
            ttl = await redis_client.client.ttl(key)
            if ttl <= 0:
                await redis_client.client.delete(key)
    except Exception as e:
        logger_main.error(f"Error clearing cache: {str(e)}")
        log_exception(f"Error clearing cache: {str(e)}", e)

async def start_cache_cleanup():
    while True:
        await clear_expired_cache()
        await asyncio.sleep(300)

def clean_ticker_for_serialization(ticker):
    if not isinstance(ticker, dict):
        return ticker
    cleaned_ticker = {}
    try:
        for key, value in ticker.items():
            if value is None:
                cleaned_ticker[key] = 0
            elif isinstance(value, (dict, list)):
                cleaned_ticker[key] = clean_ticker_for_serialization(value)
            elif isinstance(value, (int, float, str, bool)):
                cleaned_ticker[key] = value
            else:
                cleaned_ticker[key] = str(value)
        return cleaned_ticker
    except Exception as e:
        logger_main.error(f"Error cleaning ticker for serialization: {str(e)}")
        log_exception(f"Error cleaning ticker: {str(e)}", e)
        return {}

async def get_cached_data(cache_key, retries=3, base_delay=2):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    cached_data = None
    for attempt in range(retries):
        try:
            cached_data = await redis_client.get(cache_key)
            break
        except Exception as e:
            logger_main.error(f"Error fetching cached data (attempt {attempt + 1}/{retries}): {str(e)}")
            log_exception(f"Error fetching cached data: {str(e)}", e)
            if attempt < retries - 1:
                await asyncio.sleep(base_delay * (attempt + 1))
            else:
                cached_data = None
    return cached_data

async def cache_data(cache_key, data, ttl=CACHE_TTL):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    try:
        cache_size = await redis_client.dbsize()
        if cache_size > MAX_CACHE_SIZE:
            await clear_expired_cache()
        await redis_client.set(cache_key, json.dumps(data), ex=ttl)
    except Exception as e:
        logger_main.error(f"Error caching data: {str(e)}")
        log_exception(f"Error caching data: {str(e)}", e)

__all__ = ['clear_expired_cache', 'start_cache_cleanup', 'clean_ticker_for_serialization', 'get_cached_data', 'cache_data']
