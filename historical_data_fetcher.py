# historical_data_fetcher.py
import traceback
from logging_setup import logger_main

async def fetch_historical_data(exchange_id, user_id, symbol, since, testnet, exchange):
    logger_main.info(f"Fetching historical data for {symbol} on {exchange_id} since {since}")
    try:
        # Убедимся, что since в миллисекундах
        since_ms = int(since * 1000)  # Преобразуем секунды в миллисекунды
        logger_main.debug(f"Fetching OHLCV data with since={since_ms}, timeframe='4h', limit=100")  # Изменили timeframe на '4h'
        data = await exchange.fetch_ohlcv(symbol, timeframe='4h', since=since_ms, limit=100)  # Изменили timeframe на '4h'
        logger_main.debug(f"Fetched OHLCV data: {data[:5]}...")
        if len(data) < 14:  # Проверяем, достаточно ли данных для RSI с периодом 14
            logger_main.warning(f"Not enough data points ({len(data)}) for {symbol} to calculate RSI with period 14")
            return None
        return data
    except Exception as e:
        logger_main.error(f"Error fetching historical data for {symbol} on {exchange_id}: {e}\n{traceback.format_exc()}")
        return None
