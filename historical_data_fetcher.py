from logging_setup import logger_main
from ohlcv_fetcher import fetch_ohlcv

async def fetch_historical_data(exchange_id, user_id, symbol, since, testnet=False):
    """Fetches historical OHLCV data for a symbol."""
    try:
        logger_main.info(f"Fetching historical data for {symbol} on {exchange_id} since {since}")
        ohlcv_data = await fetch_ohlcv(exchange_id, symbol, user_id, timeframe='1h', since=since, testnet=testnet)
        if ohlcv_data is None or ohlcv_data.empty:
            logger_main.error(f"Failed to fetch historical data for {symbol} on {exchange_id}")
            return None
        return ohlcv_data
    except Exception as e:
        logger_main.error(f"Error fetching historical data for {symbol} on {exchange_id}: {e}")
        return None

__all__ = ['fetch_historical_data']
