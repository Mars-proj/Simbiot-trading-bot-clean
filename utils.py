import pandas as pd
import numpy as np
import pandas_ta as ta
import sys
from functools import lru_cache

def log_exception(message, exception):
    """Logs an exception with full stack trace"""
    from logging_setup import logger_exceptions
    if logger_exceptions is not None:
        logger_exceptions.error(f"{message}\n{str(exception)}", exc_info=True)
    else:
        print(f"Exception logging failed: {message}\n{str(exception)}", file=sys.stderr)

@lru_cache(maxsize=128)
def calculate_dynamic_rsi_thresholds(df_tuple, market_conditions=None, lookback_period=720):
    """
    Calculates dynamic RSI thresholds based on historical quantiles and market conditions.
    Arguments:
    - df_tuple: Tuple representation of DataFrame with OHLCV data (to make it hashable for caching).
    - market_conditions: Dictionary with market conditions (avg_volatility, avg_drop).
    - lookback_period: Lookback period for quantile calculation (default 720 hours = 30 days on 4h timeframe).
    Returns:
    - rsi_buy: Dynamic threshold for buying.
    - rsi_sell: Dynamic threshold for selling.
    """
    from logging_setup import logger_main
    # Convert tuple back to DataFrame
    df = pd.DataFrame(df_tuple, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    logger_main.info("Calculating dynamic RSI thresholds")
    try:
        # Check if there is enough data
        if len(df) < 14:
            logger_main.info("Not enough data to calculate RSI, returning default thresholds")
            return 30.0, 70.0
        # Calculate RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        # Dynamically adjust lookback_period based on volatility
        if market_conditions:
            avg_volatility = market_conditions.get('avg_volatility', 0.0)
            if avg_volatility > 0.1:  # High volatility
                lookback_period = int(lookback_period * 0.5)  # Reduce period for faster reaction
                logger_main.info(f"High volatility ({avg_volatility:.4f}), reducing lookback_period to {lookback_period}")
            elif avg_volatility < 0.05:  # Low volatility
                lookback_period = int(lookback_period * 1.5)  # Increase period for more stability
                logger_main.info(f"Low volatility ({avg_volatility:.4f}), increasing lookback_period to {lookback_period}")
        # Limit the period for quantile calculation
        rsi_data = df['rsi'].tail(lookback_period).dropna()
        if len(rsi_data) < 14:
            logger_main.info("Not enough data to calculate RSI quantiles, returning default thresholds")
            return 30.0, 70.0
        # Calculate RSI quantiles (40th and 70th percentiles)
        rsi_buy = np.percentile(rsi_data, 40)  # Increase quantile for buying
        rsi_sell = np.percentile(rsi_data, 70)  # Upper quantile for selling
        # Adjust thresholds based on market conditions
        if market_conditions:
            avg_volatility = market_conditions.get('avg_volatility', 0.0)
            # Widen thresholds during high volatility
            if avg_volatility > 0.1:  # High volatility
                rsi_buy *= 0.9  # Lower buy threshold
                rsi_sell *= 1.1  # Raise sell threshold
                logger_main.info(f"High volatility ({avg_volatility:.4f}), adjusting thresholds: buy={rsi_buy:.2f}, sell={rsi_sell:.2f}")
            elif avg_volatility < 0.05:  # Low volatility
                rsi_buy *= 1.1  # Raise buy threshold
                rsi_sell *= 0.9  # Lower sell threshold
                logger_main.info(f"Low volatility ({avg_volatility:.4f}), adjusting thresholds: buy={rsi_buy:.2f}, sell={rsi_sell:.2f}")
        # Limit thresholds to reasonable values
        rsi_buy = max(15.0, min(rsi_buy, 45.0))
        rsi_sell = max(55.0, min(rsi_sell, 85.0))
        logger_main.info(f"Dynamic RSI thresholds: buy at RSI < {rsi_buy:.2f}, sell at RSI > {rsi_sell:.2f}")
        return rsi_buy, rsi_sell
    except Exception as e:
        log_exception(f"Error calculating RSI thresholds: {str(e)}", e)
        return 30.0, 70.0

# Wrapper to convert DataFrame to tuple for caching
def calculate_dynamic_rsi_thresholds_wrapper(df, market_conditions=None, lookback_period=720):
    """Wrapper to convert DataFrame to tuple for caching"""
    df_tuple = tuple(map(tuple, df.values))  # Convert DataFrame to tuple of tuples
    return calculate_dynamic_rsi_thresholds(df_tuple, market_conditions, lookback_period)

__all__ = ['log_exception', 'calculate_dynamic_rsi_thresholds_wrapper']
