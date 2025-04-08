# learning/strategy_optimizer.py
import logging
import numpy as np
import pandas as pd
import redis.asyncio as redis
import json
import itertools
from backtester import backtest_strategy

logger = logging.getLogger("main")

async def get_redis_client():
    """Инициализация Redis клиента."""
    return await redis.from_url("redis://localhost:6379/0")

async def calculate_rsi(historical_data, period=14):
    """Вычисляет RSI на основе исторических данных."""
    closes = [candle['close'] for candle in historical_data]
    if len(closes) < period:
        return None

    df = pd.Series(closes)
    delta = df.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.tolist()

async def calculate_sma(historical_data, period=20):
    """Вычисляет SMA на основе исторических данных."""
    closes = [candle['close'] for candle in historical_data]
    if len(closes) < period:
        return None

    df = pd.Series(closes)
    sma = df.rolling(window=period).mean()
    return sma.tolist()

async def calculate_bollinger_bands(historical_data, period=20):
    """Вычисляет Bollinger Bands на основе исторических данных."""
    closes = [candle['close'] for candle in historical_data]
    if len(closes) < period:
        return None, None, None

    df = pd.Series(closes)
    sma = df.rolling(window=period).mean()
    std = df.rolling(window=period).std()
    upper_band = sma + 2 * std
    lower_band = sma - 2 * std
    return sma.tolist(), upper_band.tolist(), lower_band.tolist()

async def calculate_cci(historical_data, period=20):
    """Вычисляет CCI на основе исторических данных."""
    highs = [candle['high'] for candle in historical_data]
    lows = [candle['low'] for candle in historical_data]
    closes = [candle['close'] for candle in historical_data]
    if len(closes) < period:
        return None

    df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['sma_tp'] = df['tp'].rolling(window=period).mean()
    df['mad'] = df['tp'].rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    df['cci'] = (df['tp'] - df['sma_tp']) / (0.015 * df['mad'])
    return df['cci'].tolist()

async def generate_strategy_combinations(indicators, thresholds):
    """Генерирует комбинации индикаторов и пороговых значений."""
    strategies = []
    indicator_combinations = list(itertools.combinations(indicators, 2))  # Комбинации из 2 индикаторов

    for ind1, ind2 in indicator_combinations:
        for low1, high1 in thresholds[ind1]:
            for low2, high2 in thresholds[ind2]:
                strategy = {
                    "indicators": [
                        {"name": ind1, "low": low1, "high": high1},
                        {"name": ind2, "low": low2, "high": high2}
                    ],
                    "profit": 0
                }
                strategies.append(strategy)
    return strategies

async def evaluate_strategy(historical_data, strategy):
    """Оценивает стратегию на исторических данных."""
    indicators = strategy["indicators"]
    signals = []

    # Calculate indicators
    indicator_values = {}
    for ind in indicators:
        name = ind["name"]
        if name == "rsi":
            indicator_values[name] = await calculate_rsi(historical_data)
        elif name == "sma":
            short_sma = await calculate_sma(historical_data, period=10)
            long_sma = await calculate_sma(historical_data, period=20)
            indicator_values[name] = (short_sma, long_sma)
        elif name == "bollinger":
            sma, upper, lower = await calculate_bollinger_bands(historical_data)
            indicator_values[name] = (sma, upper, lower)
        elif name == "cci":
            indicator_values[name] = await calculate_cci(historical_data)

    # Generate signals
    for i in range(len(historical_data)):
        signal = None
        ind1 = indicators[0]
        ind2 = indicators[1]

        val1 = indicator_values[ind1["name"]][i] if ind1["name"] != "sma" else indicator_values[ind1["name"]][0][i] > indicator_values[ind1["name"]][1][i]
        val2 = indicator_values[ind2["name"]][i] if ind2["name"] != "sma" else indicator_values[ind2["name"]][0][i] > indicator_values[ind2["name"]][1][i]

        if ind1["name"] == "bollinger":
            price = historical_data[i]['close']
            upper = indicator_values["bollinger"][1][i]
            lower = indicator_values["bollinger"][2][i]
            val1 = price <= lower if ind1["low"] == "lower" else price >= upper
        if ind2["name"] == "bollinger":
            price = historical_data[i]['close']
            upper = indicator_values["bollinger"][1][i]
            lower = indicator_values["bollinger"][2][i]
            val2 = price <= lower if ind2["low"] == "lower" else price >= upper

        if ind1["name"] in ["rsi", "cci"]:
            if val1 < ind1["low"]:
                signal = "buy" if signal is None else signal
            elif val1 > ind1["high"]:
                signal = "sell" if signal is None else signal
        if ind2["name"] in ["rsi", "cci"]:
            if val2 < ind2["low"]:
                signal = "buy" if signal is None else signal
            elif val2 > ind2["high"]:
                signal = "sell" if signal is None else signal

        if ind1["name"] == "sma" and val1:
            signal = "buy" if signal is None else signal
        elif ind1["name"] == "sma" and not val1:
            signal = "sell" if signal is None else signal
        if ind2["name"] == "sma" and val2:
            signal = "buy" if signal is None else signal
        elif ind2["name"] == "sma" and not val2:
            signal = "sell" if signal is None else signal

        signals.append(signal)

    # Backtest the strategy
    profit = await backtest_strategy(historical_data, signals)
    return profit

async def optimize_strategies(exchange, symbol, timeframe='4h', limit=200):
    """Генерирует и оптимизирует новые стратегии."""
    try:
        # Fetch historical data
        historical_data = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not historical_data or len(historical_data) < limit:
            logger.warning(f"Insufficient historical data for {symbol}")
            return []

        # Define indicators and thresholds
        indicators = ["rsi", "sma", "bollinger", "cci"]
        thresholds = {
            "rsi": [(30, 70), (35, 65), (40, 60)],
            "sma": [(True, False)],  # True for short > long (buy), False for short < long (sell)
            "bollinger": [("lower", "upper")],  # Buy at lower band, sell at upper band
            "cci": [(-100, 100), (-80, 80), (-50, 50)]
        }

        # Generate strategy combinations
        strategies = await generate_strategy_combinations(indicators, thresholds)
        logger.info(f"Generated {len(strategies)} strategy combinations for {symbol}")

        # Evaluate each strategy
        for strategy in strategies:
            profit = await evaluate_strategy(historical_data, strategy)
            strategy["profit"] = profit
            logger.debug(f"Evaluated strategy {strategy['indicators']}: profit={profit}")

        # Sort strategies by profit and select top 3
        strategies.sort(key=lambda x: x["profit"], reverse=True)
        top_strategies = strategies[:3]

        # Save top strategies to Redis
        redis_client = await get_redis_client()
        try:
            strategy_key = f"custom_strategies:{symbol}"
            await redis_client.set(strategy_key, json.dumps(top_strategies), ex=86400 * 30)
            logger.info(f"Saved top strategies for {symbol}: {top_strategies}")
        finally:
            await redis_client.close()

        return top_strategies
    except Exception as e:
        logger.error(f"Failed to optimize strategies for {symbol}: {type(e).__name__}: {str(e)}")
        return []
