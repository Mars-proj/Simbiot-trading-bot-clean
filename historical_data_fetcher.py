import pandas as pd
from logging_setup import logger_main
from exchange_factory import create_exchange
from symbol_handler import validate_symbol
from config_keys import SUPPORTED_EXCHANGES

async def fetch_historical_data(exchange_id, user_id, symbol, timeframe='1d', since=None, limit=1000, testnet=False):
    """Fetches historical OHLCV data for backtesting."""
    try:
        # Validate inputs
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return None
        if not user_id or not isinstance(user_id, str):
            logger_main.error(f"Invalid user_id: {user_id}")
            return None
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        # Create exchange instance
        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None

        # Convert since to milliseconds if provided
        if since:
            since = int(since * 1000)  # Convert seconds to milliseconds

        # Fetch historical OHLCV data
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        if not ohlcv:
            logger_main.error(f"No historical data returned for {symbol} on {exchange_id}")
            return None

        # Convert to DataFrame
        data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')  # Convert timestamp to datetime

        logger_main.info(f"Fetched {len(data)} historical data points for {symbol} on {exchange_id}")
        return data
    except Exception as e:
        logger_main.error(f"Error fetching historical data for {symbol} on {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['fetch_historical_data']
