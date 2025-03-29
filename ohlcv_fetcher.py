import asyncio
from collections import OrderedDict
from logging_setup import logger_main
from async_ohlcv_fetcher import AsyncOHLCVFetcher

# Кэш для OHLCV-данных с ограничением по размеру
symbol_data_cache = OrderedDict()
MAX_CACHE_SIZE = 1000  # Максимальное количество записей в кэше
semaphore = asyncio.Semaphore(10)  # Ограничение на 10 параллельных запросов

async def fetch_ohlcv_with_cache(exchange, symbol, timeframe, limit, cache_key):
    """Загружает OHLCV-данные с кэшированием"""
    async with semaphore:
        # Создаём временный объект AsyncOHLCVFetcher для каждого запроса
        fetcher = AsyncOHLCVFetcher(exchange, semaphore)
        ohlcv = await fetcher.fetch_ohlcv(exchange, symbol, timeframe, limit)
        if ohlcv is not None:
            symbol_data_cache[cache_key] = ohlcv
            # Ограничиваем размер кэша
            if len(symbol_data_cache) > MAX_CACHE_SIZE:
                symbol_data_cache.popitem(last=False)
        return symbol, ohlcv

__all__ = ['fetch_ohlcv_with_cache', 'symbol_data_cache']
