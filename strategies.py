import pandas as pd
import ccxt.async_support as ccxt
from genetic_optimizer import GeneticOptimizer

async def optimize_rsi_thresholds(exchange, symbol, timeframe, since, limit):
    """
    Optimize RSI thresholds using genetic algorithms.

    Args:
        exchange: Exchange instance.
        symbol (str): Trading symbol.
        timeframe (str): Timeframe for OHLCV data.
        since (int): Timestamp to fetch from (in milliseconds).
        limit (int): Number of candles to fetch.

    Returns:
        dict: Optimized RSI thresholds.
    """
    optimizer = GeneticOptimizer(exchange, symbol, timeframe, since, limit)
    best_params = await optimizer.optimize()
    return {
        "buy_threshold": best_params[0] * 100,  # Преобразуем в диапазон 0-100
        "sell_threshold": best_params[1] * 100
    }

def sma_strategy(data):
    """
    Simple Moving Average trading strategy.

    Args:
        data (pd.DataFrame): OHLCV data.

    Returns:
        str: Trading signal ('buy' or 'sell').
    """
    sma_20 = data['close'].rolling(window=20).mean()
    return "buy" if data['close'].iloc[-1] > sma_20.iloc[-1] else "sell"

def rsi_strategy(data, buy_threshold=30, sell_threshold=70):
    """
    RSI trading strategy with dynamic thresholds.

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
    return "buy" if rsi.iloc[-1] < buy_threshold else "sell" if rsi.iloc[-1] > sell_threshold else "hold"
