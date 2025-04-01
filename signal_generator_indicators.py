import pandas as pd
import numpy as np
from logging_setup import logger_main
try:
    import cupy as cp
    USE_GPU = True
except ImportError:
    USE_GPU = False
    logger_main.warning("CuPy not available, falling back to NumPy for indicator calculations")

def calculate_rsi(data, period=14):
    """Calculates the Relative Strength Index (RSI) for a given data series."""
    try:
        if not isinstance(data, (pd.Series, np.ndarray)):
            logger_main.error(f"Data must be a pandas Series or numpy array, got {type(data)}")
            return None
        if len(data) < period:
            logger_main.error(f"Data length {len(data)} is less than period {period}")
            return None

        # Convert to numpy array if pandas Series
        if isinstance(data, pd.Series):
            data = data.values

        # Use CuPy if available, otherwise NumPy
        if USE_GPU:
            data = cp.array(data)
            delta = cp.diff(data)
            gain = cp.where(delta > 0, delta, 0)
            loss = cp.where(delta < 0, -delta, 0)
            avg_gain = cp.zeros(len(data))
            avg_loss = cp.zeros(len(data))
            avg_gain[period] = cp.mean(gain[1:period + 1])
            avg_loss[period] = cp.mean(loss[1:period + 1])
            for i in range(period + 1, len(data)):
                avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i]) / period
                avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i]) / period
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi = cp.where(avg_loss == 0, 100, rsi)  # Handle division by zero
            rsi = cp.asnumpy(rsi)  # Convert back to NumPy
        else:
            delta = np.diff(data)
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            avg_gain = np.zeros(len(data))
            avg_loss = np.zeros(len(data))
            avg_gain[period] = np.mean(gain[1:period + 1])
            avg_loss[period] = np.mean(loss[1:period + 1])
            for i in range(period + 1, len(data)):
                avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i - 1]) / period
                avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i - 1]) / period
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi = np.where(avg_loss == 0, 100, rsi)  # Handle division by zero

        # Convert back to pandas Series
        rsi_series = pd.Series(rsi, index=data.index if isinstance(data, pd.Series) else range(len(data)))
        logger_main.info(f"Calculated RSI with period {period} using {'CuPy' if USE_GPU else 'NumPy'}")
        return rsi_series
    except Exception as e:
        logger_main.error(f"Error calculating RSI: {e}")
        return None

__all__ = ['calculate_rsi']
