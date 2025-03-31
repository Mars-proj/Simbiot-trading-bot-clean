import numpy as np
from logging_setup import logger_main
from global_objects import SUPPORTED_SYMBOLS

try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    cp = np  # Fallback to numpy if cupy is not available
    logger_main.warning("CuPy not available, falling back to NumPy for RSI calculation")

def calculate_rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
    """Calculates RSI with GPU acceleration if available, otherwise uses NumPy."""
    try:
        # Convert data to cupy array if GPU is available, otherwise use numpy
        data = cp.asarray(data) if GPU_AVAILABLE else np.asarray(data)
        delta = cp.diff(data)
        gain = cp.where(delta > 0, delta, 0)
        loss = cp.where(delta < 0, -delta, 0)

        avg_gain = cp.zeros_like(data)
        avg_loss = cp.zeros_like(data)

        # Initial average
        avg_gain[period] = cp.mean(gain[:period])
        avg_loss[period] = cp.mean(loss[:period])

        # Smoothing
        for i in range(period + 1, len(data)):
            avg_gain[i] = (avg_gain[i-1] * (period - 1) + gain[i]) / period
            avg_loss[i] = (avg_loss[i-1] * (period - 1) + loss[i]) / period

        rs = avg_gain / (avg_loss + 1e-10)  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        logger_main.info(f"Calculated RSI {'on GPU' if GPU_AVAILABLE else 'on CPU'} for period {period}")
        return cp.asnumpy(rsi) if GPU_AVAILABLE else rsi
    except Exception as e:
        logger_main.error(f"Error calculating RSI: {e}")
        return None

__all__ = ['calculate_rsi']
