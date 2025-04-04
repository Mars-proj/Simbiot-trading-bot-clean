# historical_data_fetcher.py
import traceback
from logging_setup import logger_main

async def fetch_historical_data(exchange_id, user_id, symbol, since, testnet, exchange):
    logger_main.info(f"Fetching historical data for {symbol} on {exchange_id} since {since}")
    try:
        # Убедимся, что since в миллисекундах
        since_ms = int(since * 1000)  # Преобразуем секунды в миллисекунды
        logger_main.debug(f"Fetching OHLCV data with since={since_ms}, timeframe='1d', limit=30")
        data = await exchange.fetch_ohlcv(symbol, timeframe='1d', since=since_ms, limit=30)
        logger_main.debug(f"Fetched OHLCV data: {data[:5]}...")
        return data
    except Exception as e:
        logger_main.error(f"Error fetching historical data for {symbol} on {exchange_id}: {e}\n{traceback.format_exc()}")
        return None
