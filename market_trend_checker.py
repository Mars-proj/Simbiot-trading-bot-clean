import pandas as pd
from logging_setup import logger_main

def check_trend(data, short_ema_period=20, long_ema_period=50):
    """Checks the market trend based on OHLCV data using EMA."""
    try:
        if not isinstance(data, pd.DataFrame):
            logger_main.error(f"Data must be a pandas DataFrame, got {type(data)}")
            return None
        required_columns = ['close']
        for col in required_columns:
            if col not in data.columns:
                logger_main.error(f"Missing required column: {col}")
                return None

        # Calculate EMAs for trend analysis
        short_ema = data['close'].ewm(span=short_ema_period, adjust=False).mean().iloc[-1]
        long_ema = data['close'].ewm(span=long_ema_period, adjust=False).mean().iloc[-1]
        trend = 'up' if short_ema > long_ema else 'down'
        logger_main.info(f"Trend for data: {trend} (short_ema={short_ema}, long_ema={long_ema})")
        return trend
    except Exception as e:
        logger_main.error(f"Error checking trend: {e}")
        return None

__all__ = ['check_trend']
