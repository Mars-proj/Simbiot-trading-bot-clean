import pandas as pd
import ccxt.async_support as ccxt
import numpy as np
from genetic_optimizer import GeneticOptimizer

async def optimize_thresholds(exchange, symbol, timeframe, since, limit, strategy_type):
    """
    Optimize thresholds for a strategy using genetic algorithms.

    Args:
        exchange: Exchange instance.
        symbol (str): Trading symbol.
        timeframe (str): Timeframe for OHLCV data.
        since (int): Timestamp to fetch from (in milliseconds).
        limit (int): Number of candles to fetch.
        strategy_type (str): Type of strategy ('rsi', 'macd', 'bb', 'vw').

    Returns:
        dict: Optimized thresholds.
    """
    optimizer = GeneticOptimizer(exchange, symbol, timeframe, since, limit)
    best_params = await optimizer.optimize()
    if strategy_type == "rsi":
        return {
            "buy_threshold": best_params[0] * 100,  # Преобразуем в диапазон 0-100
            "sell_threshold": best_params[1] * 100
        }
    elif strategy_type == "macd":
        return {
            "fast_period": int(best_params[0] * 20 + 5),  # Диапазон 5-25
            "slow_period": int(best_params[1] * 40 + 10),  # Диапазон 10-50
            "signal_period": int(best_params[2] * 10 + 3)  # Диапазон 3-13
        }
    elif strategy_type == "bb":
        return {
            "period": int(best_params[0] * 20 + 10),  # Диапазон 10-30
            "std_dev": best_params[1] * 2 + 1  # Диапазон 1-3
        }
    elif strategy_type == "vw":
        return {
            "volume_weight": best_params[0] * 2  # Диапазон 0-2
        }
    return {}

def sma_crossover_strategy(data):
    """
    SMA Crossover trading strategy (fast SMA vs slow SMA).

    Args:
        data (pd.DataFrame): OHLCV data.

    Returns:
        str: Trading signal ('buy', 'sell', or 'hold').
    """
    sma_fast = data['close'].rolling(window=10).mean()
    sma_slow = data['close'].rolling(window=50).mean()
    if sma_fast.iloc[-1] > sma_slow.iloc[-1] and sma_fast.iloc[-2] <= sma_slow.iloc[-2]:
        return "buy"
    elif sma_fast.iloc[-1] < sma_slow.iloc[-1] and sma_fast.iloc[-2] >= sma_slow.iloc[-2]:
        return "sell"
    return "hold"

def rsi_divergence_strategy(data, buy_threshold=30, sell_threshold=70):
    """
    RSI Divergence trading strategy with dynamic thresholds.

    Args:
        data (pd.DataFrame): OHLCV data.
        buy_threshold (float): RSI buy threshold (default: 30).
        sell_threshold (float): RSI sell threshold (default: 70).

    Returns:
        str: Trading signal ('buy', 'sell', or 'hold').
    """
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Проверяем дивергенцию
    price_diff = data['close'].diff()
    rsi_diff = rsi.diff()
    bullish_divergence = (price_diff.iloc[-1] < 0 and rsi_diff.iloc[-1] > 0 and rsi.iloc[-1] < buy_threshold)
    bearish_divergence = (price_diff.iloc[-1] > 0 and rsi_diff.iloc[-1] < 0 and rsi.iloc[-1] > sell_threshold)

    if bullish_divergence:
        return "buy"
    elif bearish_divergence:
        return "sell"
    elif rsi.iloc[-1] < buy_threshold:
        return "buy"
    elif rsi.iloc[-1] > sell_threshold:
        return "sell"
    return "hold"

def macd_crossover_strategy(data, fast_period=12, slow_period=26, signal_period=9):
    """
    MACD Crossover trading strategy with dynamic periods.

    Args:
        data (pd.DataFrame): OHLCV data.
        fast_period (int): Fast EMA period (default: 12).
        slow_period (int): Slow EMA period (default: 26).
        signal_period (int): Signal line period (default: 9).

    Returns:
        str: Trading signal ('buy', 'sell', or 'hold').
    """
    exp1 = data['close'].ewm(span=fast_period, adjust=False).mean()
    exp2 = data['close'].ewm(span=slow_period, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal_period, adjust=False).mean()

    if macd.iloc[-1] > signal_line.iloc[-1] and macd.iloc[-2] <= signal_line.iloc[-2]:
        return "buy"
    elif macd.iloc[-1] < signal_line.iloc[-1] and macd.iloc[-2] >= signal_line.iloc[-2]:
        return "sell"
    return "hold"

def bollinger_breakout_strategy(data, period=20, std_dev=2):
    """
    Bollinger Bands Breakout trading strategy with dynamic parameters.

    Args:
        data (pd.DataFrame): OHLCV data.
        period (int): Period for SMA and STD (default: 20).
        std_dev (float): Standard deviation multiplier (default: 2).

    Returns:
        str: Trading signal ('buy', 'sell', or 'hold').
    """
    sma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)

    if data['close'].iloc[-1] > upper_band.iloc[-1] and data['close'].iloc[-2] <= upper_band.iloc[-2]:
        return "buy"
    elif data['close'].iloc[-1] < lower_band.iloc[-1] and data['close'].iloc[-2] >= lower_band.iloc[-2]:
        return "sell"
    return "hold"

def volume_weighted_trend_strategy(data, volume_weight=1.0):
    """
    Volume-Weighted Trend trading strategy with dynamic weight.

    Args:
        data (pd.DataFrame): OHLCV data.
        volume_weight (float): Weight of volume in trend calculation (default: 1.0).

    Returns:
        str: Trading signal ('buy', 'sell', or 'hold').
    """
    sma_20 = data['close'].rolling(window=20).mean()
    volume_sma = data['volume'].rolling(window=20).mean()
    weighted_trend = (data['close'] - sma_20) * (data['volume'] / volume_sma) * volume_weight
    if weighted_trend.iloc[-1] > 0 and weighted_trend.iloc[-2] <= 0:
        return "buy"
    elif weighted_trend.iloc[-1] < 0 and weighted_trend.iloc[-2] >= 0:
        return "sell"
    return "hold"
