import pandas as pd
import asyncio
from logging_setup import logger_main

async def analyze_token(exchange_id, user_id, symbol, timeframe='1h', limit=100, testnet=False, exchange=None):
    """Analyzes token market data (volume, volatility)."""
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
        # Fetch OHLCV data
        from ohlcv_fetcher import fetch_ohlcv
        ohlcv_data = await fetch_ohlcv(exchange_id, symbol, user_id, timeframe=timeframe, limit=limit, testnet=testnet, exchange=exchange)
        if ohlcv_data is None or ohlcv_data.empty:
            logger_main.error(f"Failed to fetch OHLCV data for {symbol} on {exchange_id}")
            return None

        # Calculate total volume
        total_volume = ohlcv_data['volume'].sum()

        # Calculate volatility (standard deviation of returns)
        returns = ohlcv_data['close'].pct_change().dropna()
        volatility = returns.std() * 100  # Convert to percentage

        result = {
            'total_volume': total_volume,
            'volatility': volatility
        }
        logger_main.info(f"Token analysis for {symbol} on {exchange_id}: volume={total_volume}, volatility={volatility}%")
        return result
    except Exception as e:
        logger_main.error(f"Error analyzing token {symbol} on {exchange_id}: {e}")
        return None
    finally:
        if should_close and exchange is not None:
            logger_main.info(f"Closing exchange connection in token_analyzer for {exchange_id}")
            await exchange.close()

__all__ = ['analyze_token']
