import pandas as pd
import numpy as np
from logging_setup import logger_main

def calculate_moving_average(data, window=20):
    """Calculates the moving average for a given data series."""
    try:
        if len(data) < window:
            logger_main.error(f"Data length {len(data)} is less than window size {window}")
            return None
        ma = data.rolling(window=window).mean()
        logger_main.debug(f"Calculated moving average with window {window}")
        return ma
    except Exception as e:
        logger_main.error(f"Error calculating moving average: {e}")
        return None

def calculate_bollinger_bands(data, window=20, num_std=2):
    """Calculates Bollinger Bands for a given data series."""
    try:
        if len(data) < window:
            logger_main.error(f"Data length {len(data)} is less than window size {window}")
            return None, None
        rolling_mean = data.rolling(window=window).mean()
        rolling_std = data.rolling(window=window).std()
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)
        logger_main.debug(f"Calculated Bollinger Bands with window {window} and {num_std} standard deviations")
        return upper_band, lower_band
    except Exception as e:
        logger_main.error(f"Error calculating Bollinger Bands: {e}")
        return None, None

__all__ = ['calculate_moving_average', 'calculate_bollinger_bands']
