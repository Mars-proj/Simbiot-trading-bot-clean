# test_symbols.py
import ccxt.async_support as ccxt
from logging_setup import logger_main
from cache_utils import RedisClient

async def get_test_symbols(exchange_pool, exchange_id, user_id, testnet=False):
    cache = RedisClient(f"redis://localhost:6379")
    cache_key = f"test_symbols:{exchange_id}:{user_id}"
    cached_symbols = cache.get_list(cache_key)
    if cached_symbols:
        logger_main.info(f"Returning cached symbols for {cache_key}: {cached_symbols[:5]}...")
        return cached_symbols

    logger_main.info(f"Fetching test symbols for {exchange_id}:{user_id}")
    exchange = await exchange_pool.get_exchange(exchange_id, user_id, testnet)
    try:
        markets = await exchange.load_markets()
        symbols = [symbol for symbol in markets.keys() if symbol.endswith('USDT')]
        cache.set_list(cache_key, symbols)
        logger_main.info(f"Fetched {len(symbols)} symbols for {exchange_id}:{user_id}: {symbols[:5]}...")
        return symbols
    finally:
        await exchange.close()
