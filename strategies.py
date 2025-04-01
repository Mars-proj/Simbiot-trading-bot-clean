import pandas as pd
from logging_setup import logger_main

def recommend_strategy(data, short_period=20, long_period=50):
    """Recommends a trading strategy based on moving averages."""
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

        # Calculate moving averages
        short_ma = data['close'].rolling(window=short_period).mean()
        long_ma = data['close'].rolling(window=long_period).mean()

        # Determine strategy
        latest_short_ma = short_ma.iloc[-1]
        latest_long_ma = long_ma.iloc[-1]
        if latest_short_ma > latest_long_ma:
            strategy = 'buy'  # Trend-following: go long
        elif latest_short_ma < latest_long_ma:
            strategy = 'sell'  # Trend-following: go short
        else:
            strategy = 'hold'  # Neutral

        logger_main.info(f"Recommended strategy: {strategy} (short_ma={latest_short_ma:.2f}, long_ma={latest_long_ma:.2f})")
        return strategy
    except Exception as e:
        logger_main.error(f"Error recommending strategy: {e}")
        return None

__all__ = ['recommend_strategy']
