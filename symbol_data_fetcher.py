import asyncio
from data_fetcher import fetch_ohlcv
from utils import logger_main

async def fetch_ohlcv_for_symbol(exchange, symbol):
    """Получение OHLCV-данных для символа"""
    logger_main.debug(f"Начало загрузки OHLCV для символа {symbol}")
    try:
        ohlcv = await fetch_ohlcv(exchange, symbol, timeframe='4h', limit=100)
        if ohlcv is None:
            logger_main.warning(f"OHLCV для {symbol} не загружен (None)")
        else:
            logger_main.debug(f"OHLCV для {symbol} успешно загружен: {ohlcv.tail(1).to_dict()}")
        return symbol, ohlcv
    except Exception as e:
        logger_main.error(f"Ошибка при загрузке OHLCV для {symbol}: {str(e)}")
        return symbol, None

__all__ = ['fetch_ohlcv_for_symbol']
