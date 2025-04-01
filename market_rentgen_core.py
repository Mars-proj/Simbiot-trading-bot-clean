import pandas as pd
from logging_setup import logger_main
from exchange_utils import fetch_ticker
from ohlcv_fetcher import fetch_ohlcv
from symbol_handler import validate_symbol

async def analyze_market(exchange, symbol, timeframe='1h', limit=100):
    """Analyzes market conditions for a symbol, including trend and volatility."""
    try:
        if not await validate_symbol(exchange.id, exchange.user_id, symbol, testnet=exchange.testnet):
            logger_main.error(f"Invalid symbol: {symbol}")
            return None

        # Fetch OHLCV data
        ohlcv_data = await fetch_ohlcv(exchange.id, symbol, exchange.user_id, timeframe=timeframe, limit=limit, as_dataframe=True)
        if ohlcv_data is None or ohlcv_data.empty:
            logger_main.error(f"Failed to fetch OHLCV data for {symbol} on {exchange.id}")
            return None

        # Calculate trend (using simple moving averages)
        short_ma = ohlcv_data['close'].rolling(window=20).mean()
        long_ma = ohlcv_data['close'].rolling(window=50).mean()
        latest_short_ma = short_ma.iloc[-1]
        latest_long_ma = long_ma.iloc[-1]
        trend = 'bullish' if latest_short_ma > latest_long_ma else 'bearish' if latest_short_ma < latest_long_ma else 'neutral'

        # Calculate volatility
        volatility = ohlcv_data['close'].pct_change().rolling(window=20).std().iloc[-1] * 100  # in percentage

        # Fetch current ticker
        ticker = await fetch_ticker(exchange, symbol)
        if not ticker:
            logger_main.error(f"Failed to fetch ticker for {symbol} on {exchange.id}")
            return None

        analysis = {
            'symbol': symbol,
            'trend': trend,
            'volatility': volatility,
            'last_price': ticker.get('last'),
            'bid': ticker.get('bid'),
            'ask': ticker.get('ask')
        }

        logger_main.info(f"Market analysis for {symbol} on {exchange.id}: trend={trend}, volatility={volatility:.2f}%")
        return analysis
    except Exception as e:
        logger_main.error(f"Error analyzing market for {symbol} on {exchange.id}: {e}")
        return None

__all__ = ['analyze_market']
