import pandas as pd
import asyncio
from logging_setup import logger_main
from config_keys import SUPPORTED_EXCHANGES

async def fetch_ohlcv(exchange_id, symbol, user_id, timeframe='1h', limit=100, testnet=False, exchange=None):
    """Fetches OHLCV data from the exchange."""
    if exchange is None:
        from exchange_factory import create_exchange
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None
        should_close = True
    else:
        should_close = False

    try:
        # Validate inputs
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return None
        if not user_id or not isinstance(user_id, str):
            logger_main.error(f"Invalid user_id: {user_id}")
            return None

        # Fetch OHLCV data
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv:
            logger_main.info(f"No OHLCV data for {symbol} on {exchange_id}")
            return None

        # Convert to DataFrame
        data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')  # Convert timestamp to datetime

        logger_main.info(f"Fetched {len(data)} OHLCV data points for {symbol} on {exchange_id}")
        return data
    except Exception as e:
        logger_main.error(f"Error fetching OHLCV data for {symbol} on {exchange_id}: {e}")
        return None
    finally:
        if should_close and exchange is not None:
            logger_main.info(f"Closing exchange connection in ohlcv_fetcher for {exchange_id}")
            await exchange.close()

__all__ = ['fetch_ohlcv']
