import pandas as pd
import numpy as np
from logging_setup import logger_main

def calculate_rsi(data, periods=14):
    """Calculates the Relative Strength Index (RSI)."""
    try:
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except Exception as e:
        logger_main.error(f"Error calculating RSI: {e}")
        return None

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """Calculates the MACD and Signal Line."""
    try:
        exp1 = data.ewm(span=fast_period, adjust=False).mean()
        exp2 = data.ewm(span=slow_period, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        return macd, signal
    except Exception as e:
        logger_main.error(f"Error calculating MACD: {e}")
        return None, None

__all__ = ['calculate_rsi', 'calculate_macd']
