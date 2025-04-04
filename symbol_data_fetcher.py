# symbol_data_fetcher.py
from logging_setup import logger_main
from cache_utils import RedisClient  # Заменили CacheUtils на RedisClient

async def fetch_symbol_data(exchange_id, user_id, symbol, testnet=False):
    cache = RedisClient(f"redis://localhost:6379")  # Заменили CacheUtils на RedisClient
    cache_key = f"symbol_data:{exchange_id}:{user_id}:{symbol}"
    cached_data = cache.get_list(cache_key)
    if cached_data:
        logger_main.info(f"Returning cached symbol data for {cache_key}")
        return cached_data

    logger_main.info(f"Fetching symbol data for {symbol} on {exchange_id}")
    # Здесь логика получения данных о символе
    data = []  # Заглушка
    cache.set_list(cache_key, data)
    return data
