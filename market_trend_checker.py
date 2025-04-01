import pandas as pd
from logging_setup import logger_main

def check_market_trend(data, short_period=20, long_period=50):
    """Checks the market trend using exponential moving averages."""
    try:
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Data must be a pandas DataFrame, got {type(data)}")
            return None
        if data.empty:
            logger_main.error("DataFrame is empty")
            return None
        if 'close' not in data.columns:
            logger_main.error("DataFrame must contain a 'close' column")
            return None

        # Calculate EMAs
        short_ema = data['close'].ewm(span=short_period, adjust=False).mean()
        long_ema = data['close'].ewm(span=long_period, adjust=False).mean()

        # Determine trend
        latest_short_ema = short_ema.iloc[-1]
        latest_long_ema = long_ema.iloc[-1]
        trend = 'bullish' if latest_short_ema > latest_long_ema else 'bearish' if latest_short_ema < latest_long_ema else 'neutral'

        logger_main.info(f"Market trend: {trend} (short_ema={latest_short_ema:.2f}, long_ema={latest_long_ema:.2f})")
        return trend
    except Exception as e:
        logger_main.error(f"Error checking market trend: {e}")
        return None

__all__ = ['check_market_trend']
