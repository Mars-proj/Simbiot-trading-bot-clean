import ccxt.async_support as ccxt
import pandas as pd
from logging_setup import logger_main
from exchange_utils import fetch_ticker
from ohlcv_fetcher import fetch_ohlcv
from symbol_handler import validate_symbol

async def analyze_market(exchange, symbol, user_id, exchange_id, timeframe='1h', limit=100, testnet=False):
    """Analyzes market conditions for a symbol, including trend and volatility."""
    try:
        # Validate inputs
        if not isinstance(exchange, ccxt.async_support.Exchange):
            logger_main.error(f"Exchange must be a ccxt.async_support.Exchange object, got {type(exchange)}")
            return None
        if not await validate_symbol(exchange_id, user_id, symbol, testnet=testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        # Fetch ticker data
        ticker = await fetch_ticker(exchange, symbol, exchange_id, user_id, testnet=testnet)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol}")
            return None

        # Fetch OHLCV data for trend and volatility analysis
        ohlcv = await fetch_ohlcv(exchange_id, symbol, user_id, timeframe=timeframe, limit=limit, testnet=testnet, as_dataframe=True)
        if ohlcv is None or len(ohlcv) == 0:
            logger_main.error(f"Failed to fetch OHLCV data for {symbol}")
            return None

        df = ohlcv
        # Calculate trend (using a simple moving average comparison)
        short_ma = df['close'].rolling(window=20).mean().iloc[-1]
        long_ma = df['close'].rolling(window=50).mean().iloc[-1]
        trend = 'up' if short_ma > long_ma else 'down'

        # Calculate volatility (standard deviation of returns)
        returns = df['close'].pct_change()
        volatility = returns.rolling(window=20).std().iloc[-1]

        market_data = {
            'symbol': symbol,
            'price': ticker['last'],
            'volume': ticker['baseVolume'],
            'spread': ticker['ask'] - ticker['bid'],
            'trend': trend,
            'volatility': volatility
        }
        logger_main.info(f"Market analysis for {symbol}: {market_data}")
        return market_data
    except Exception as e:
        logger_main.error(f"Error analyzing market for {symbol}: {e}")
        return None

__all__ = ['analyze_market']
