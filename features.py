import pandas as pd
import numpy as np

def calculate_moving_average(data, period=20):
    """
    Calculate moving average.

    Args:
        data (pd.DataFrame): OHLCV data.
        period (int): Period for moving average (default: 20).

    Returns:
        pd.Series: Moving average values.
    """
    return data['close'].rolling(window=period).mean()

def calculate_volatility(data, period=20):
    """
    Calculate volatility.

    Args:
        data (pd.DataFrame): OHLCV data.
        period (int): Period for volatility calculation (default: 20).

    Returns:
        float: Volatility value.
    """
    returns = data['close'].pct_change()
    return returns.rolling(window=period).std() * np.sqrt(period)

def calculate_sma(data, period=20):
    """
    Calculate Simple Moving Average.

    Args:
        data (pd.DataFrame): OHLCV data.
        period (int): SMA period (default: 20).

    Returns:
        pd.Series: SMA values.
    """
    return data['close'].rolling(window=period).mean()

def calculate_rsi(data, period=14):
    """
    Calculate Relative Strength Index.

    Args:
        data (pd.DataFrame): OHLCV data.
        period (int): RSI period (default: 14).

    Returns:
        pd.Series: RSI values.
    """
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate MACD indicator.

    Args:
        data (pd.DataFrame): OHLCV data.
        fast_period (int): Fast EMA period (default: 12).
        slow_period (int): Slow EMA period (default: 26).
        signal_period (int): Signal line period (default: 9).

    Returns:
        tuple: (macd, signal_line, histogram)
    """
    exp1 = data['close'].ewm(span=fast_period, adjust=False).mean()
    exp2 = data['close'].ewm(span=slow_period, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal_period, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calculate_sharpe_ratio(data):
    """
    Calculate Sharpe ratio.

    Args:
        data (pd.DataFrame): OHLCV data.

    Returns:
        float: Sharpe ratio.
    """
    returns = data['close'].pct_change()
    return returns.mean() / returns.std() * np.sqrt(252)

def calculate_average_return(data):
    """
    Calculate average return.

    Args:
        data (pd.DataFrame): OHLCV data.

    Returns:
        float: Average return.
    """
    returns = data['close'].pct_change()
    return returns.mean() * 252

def calculate_price_to_mean(data):
    """
    Calculate the ratio of current price to historical mean.

    Args:
        data (pd.DataFrame): OHLCV data.

    Returns:
        float: Price-to-mean ratio.
    """
    return data['close'].iloc[-1] / data['close'].mean()

def calculate_trend(data):
    """
    Calculate market trend using SMA20 and SMA50.

    Args:
        data (pd.DataFrame): OHLCV data.

    Returns:
        str: Trend ('up', 'down', or 'sideways').
    """
    sma_20 = data['close'].rolling(window=20).mean()
    sma_50 = data['close'].rolling(window=50).mean()
    if sma_20.iloc[-1] > sma_50.iloc[-1]:
        return "up"
    elif sma_20.iloc[-1] < sma_50.iloc[-1]:
        return "down"
    else:
        return "sideways"

def extract_features(data):
    """
    Extract features for ML model.

    Args:
        data (pd.DataFrame): OHLCV data.

    Returns:
        np.ndarray: Feature array.
    """
    sma_20 = calculate_sma(data, period=20).iloc[-1]
    sma_50 = calculate_sma(data, period=50).iloc[-1]
    rsi = calculate_rsi(data, period=14).iloc[-1]
    volatility = calculate_volatility(data, period=20)
    macd, signal_line, _ = calculate_macd(data)
    sharpe = calculate_sharpe_ratio(data)
    avg_return = calculate_average_return(data)
    price_to_mean = calculate_price_to_mean(data)
    trend = 1 if calculate_trend(data) == "up" else -1 if calculate_trend(data) == "down" else 0
    return np.array([sma_20, sma_50, rsi, volatility, macd.iloc[-1], signal_line.iloc[-1], sharpe, avg_return, price_to_mean, trend])
