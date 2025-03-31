import pandas as pd
from logging_setup import logger_main

def calculate_sma(data, period=14):
    """Calculates Simple Moving Average (SMA)."""
    try:
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        sma = data.rolling(window=period).mean()
        logger_main.info(f"Calculated SMA with period {period}")
        return sma
    except Exception as e:
        logger_main.error(f"Error calculating SMA: {e}")
        return None

def calculate_ema(data, period=14):
    """Calculates Exponential Moving Average (EMA)."""
    try:
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        ema = data.ewm(span=period, adjust=False).mean()
        logger_main.info(f"Calculated EMA with period {period}")
        return ema
    except Exception as e:
        logger_main.error(f"Error calculating EMA: {e}")
        return None

def calculate_rsi(data, period=14):
    """Calculates Relative Strength Index (RSI)."""
    try:
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        logger_main.info(f"Calculated RSI with period {period}")
        return rsi
    except Exception as e:
        logger_main.error(f"Error calculating RSI: {e}")
        return None

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """Calculates MACD (Moving Average Convergence Divergence)."""
    try:
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        fast_ema = data.ewm(span=fast_period, adjust=False).mean()
        slow_ema = data.ewm(span=slow_period, adjust=False).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        logger_main.info(f"Calculated MACD with periods {fast_period}, {slow_period}, {signal_period}")
        return macd, signal, histogram
    except Exception as e:
        logger_main.error(f"Error calculating MACD: {e}")
        return None, None, None

def calculate_bollinger_bands(data, period=20, std_dev=2):
    """Calculates Bollinger Bands."""
    try:
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        logger_main.info(f"Calculated Bollinger Bands with period {period} and std_dev {std_dev}")
        return upper_band, sma, lower_band
    except Exception as e:
        logger_main.error(f"Error calculating Bollinger Bands: {e}")
        return None, None, None

def calculate_obv(data, volume):
    """Calculates On-Balance Volume (OBV)."""
    try:
        if not isinstance(data, pd.Series) or not isinstance(volume, pd.Series):
            data = pd.Series(data)
            volume = pd.Series(volume)
        direction = data.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        obv = (direction * volume).cumsum()
        logger_main.info("Calculated OBV")
        return obv
    except Exception as e:
        logger_main.error(f"Error calculating OBV: {e}")
        return None

def calculate_adx(high, low, close, period=14):
    """Calculates Average Directional Index (ADX)."""
    try:
        if not isinstance(high, pd.Series) or not isinstance(low, pd.Series) or not isinstance(close, pd.Series):
            high = pd.Series(high)
            low = pd.Series(low)
            close = pd.Series(close)
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        plus_dm = (high - high.shift()).where((high - high.shift()) > (low.shift() - low), 0)
        minus_dm = (low.shift() - low).where((low.shift() - low) > (high - high.shift()), 0)
        plus_di = 100 * plus_dm.rolling(window=period).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=period).mean() / atr
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        logger_main.info(f"Calculated ADX with period {period}")
        return adx
    except Exception as e:
        logger_main.error(f"Error calculating ADX: {e}")
        return None

__all__ = ['calculate_sma', 'calculate_ema', 'calculate_rsi', 'calculate_macd', 'calculate_bollinger_bands', 'calculate_obv', 'calculate_adx']
