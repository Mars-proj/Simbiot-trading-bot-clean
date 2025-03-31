import pandas as pd
from logging_setup import logger_main
from exchange_factory import create_exchange
from symbol_handler import validate_symbol

async def fetch_ohlcv(exchange_id, symbol, user_id, timeframe='1h', limit=100, testnet=False, as_dataframe=False):
    """Fetches OHLCV data for a symbol."""
    try:
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        exchange = create_exchange(exchange_id, user_id, testnet=testnet)
        if not exchange:
            logger_main.error(f"Failed to create exchange instance for {exchange_id}")
            return None

        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv:
            logger_main.error(f"No OHLCV data returned for {symbol} on {exchange_id}")
            return None

        data = {
            'timestamp': [candle[0] for candle in ohlcv],
            'open': [candle[1] for candle in ohlcv],
            'high': [candle[2] for candle in ohlcv],
            'low': [candle[3] for candle in ohlcv],
            'close': [candle[4] for candle in ohlcv],
            'volume': [candle[5] for candle in ohlcv]
        }

        if as_dataframe:
            data = pd.DataFrame(data)

        logger_main.info(f"Fetched OHLCV data for {symbol} on {exchange_id}: {len(ohlcv)} candles")
        return data
    except Exception as e:
        logger_main.error(f"Error fetching OHLCV data for {symbol} on {exchange_id}: {e}")
        return None
    finally:
        await exchange.close()

__all__ = ['fetch_ohlcv']
