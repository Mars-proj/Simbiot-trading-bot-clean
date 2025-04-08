# strategy_manager.py
import logging
import numpy as np
import pandas as pd
import redis.asyncio as redis
import json

logger = logging.getLogger("main")

async def get_redis_client():
    """Инициализация Redis клиента."""
    return await redis.from_url("redis://localhost:6379/0")

async def calculate_rsi(exchange, symbol, timeframe='4h', period=14, limit=100):
    """Вычисляет RSI для символа."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < period:
            logger.warning(f"Insufficient data to calculate RSI for {symbol}")
            return None

        closes = [candle[4] for candle in ohlcv]
        df = pd.Series(closes)

        delta = df.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]
    except Exception as e:
        logger.error(f"Failed to calculate RSI for {symbol}: {type(e).__name__}: {str(e)}")
        return None

async def calculate_sma(exchange, symbol, timeframe='4h', short_period=10, long_period=20, limit=100):
    """Вычисляет скользящие средние (короткую и длинную) для символа."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < long_period:
            logger.warning(f"Insufficient data to calculate SMA for {symbol}")
            return None, None

        closes = [candle[4] for candle in ohlcv]
        df = pd.Series(closes)

        short_sma = df.rolling(window=short_period).mean().iloc[-1]
        long_sma = df.rolling(window=long_period).mean().iloc[-1]
        return short_sma, long_sma
    except Exception as e:
        logger.error(f"Failed to calculate SMA for {symbol}: {type(e).__name__}: {str(e)}")
        return None, None

async def calculate_bollinger_bands(exchange, symbol, timeframe='4h', period=20, limit=100):
    """Вычисляет Bollinger Bands для символа."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < period:
            logger.warning(f"Insufficient data to calculate Bollinger Bands for {symbol}")
            return None, None, None

        closes = [candle[4] for candle in ohlcv]
        df = pd.Series(closes)

        sma = df.rolling(window=period).mean()
        std = df.rolling(window=period).std()
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std

        return sma.iloc[-1], upper_band.iloc[-1], lower_band.iloc[-1]
    except Exception as e:
        logger.error(f"Failed to calculate Bollinger Bands for {symbol}: {type(e).__name__}: {str(e)}")
        return None, None, None

async def calculate_cci(exchange, symbol, timeframe='4h', period=20, limit=100):
    """Вычисляет CCI (Commodity Channel Index) для символа."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < period:
            logger.warning(f"Insufficient data to calculate CCI for {symbol}")
            return None

        highs = [candle[2] for candle in ohlcv]
        lows = [candle[3] for candle in ohlcv]
        closes = [candle[4] for candle in ohlcv]

        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        df['tp'] = (df['high'] + df['low'] + df['close']) / 3
        df['sma_tp'] = df['tp'].rolling(window=period).mean()
        df['mad'] = df['tp'].rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
        df['cci'] = (df['tp'] - df['sma_tp']) / (0.015 * df['mad'])

        cci = df['cci'].iloc[-1]
        return cci if not np.isnan(cci) else 0
    except Exception as e:
        logger.error(f"Failed to calculate CCI for {symbol}: {type(e).__name__}: {str(e)}")
        return 0

async def get_dynamic_thresholds(indicator, volatility, user, symbol, base_low=40, base_high=60):
    """Вычисляет динамические пороговые значения для индикатора."""
    redis_client = await get_redis_client()
    try:
        success_key = f"trade_success:{symbol}:{user}"
        success_data = await redis_client.get(success_key)
        success_rate = 0.5
        if success_data:
            success_data = json.loads(success_data.decode())
            total_trades = success_data.get('total_trades', 1)
            successful_trades = success_data.get('successful_trades', 0)
            success_rate = successful_trades / total_trades if total_trades > 0 else 0.5

        volatility_factor = 1 + (volatility / 10)
        success_factor = 1 - (success_rate - 0.5)

        if indicator == "rsi":
            low = base_low * success_factor / volatility_factor
            high = base_high * success_factor * volatility_factor
            low = max(30, min(45, low))
            high = max(55, min(70, high))
        elif indicator == "cci":
            low = -100 * success_factor / volatility_factor
            high = 100 * success_factor * volatility_factor
            low = max(-150, min(-50, low))
            high = min(150, max(50, high))
        else:
            low = base_low
            high = base_high

        return low, high
    finally:
        await redis_client.close()

async def rsi_sma_strategy(exchange, symbol, user, volatility, timeframe='4h'):
    """Стратегия для трендового рынка: RSI + SMA."""
    try:
        rsi = await calculate_rsi(exchange, symbol, timeframe)
        if rsi is None:
            return None

        short_sma, long_sma = await calculate_sma(exchange, symbol, timeframe)
        if short_sma is None or long_sma is None:
            return None

        rsi_buy, rsi_sell = await get_dynamic_thresholds("rsi", volatility, user, symbol, base_low=40, base_high=60)

        if rsi < rsi_buy and short_sma > long_sma:
            return "buy"
        elif rsi > rsi_sell and short_sma < long_sma:
            return "sell"
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to execute RSI+SMA strategy for {symbol}: {type(e).__name__}: {str(e)}")
        return None

async def bollinger_strategy(exchange, symbol, user, volatility, timeframe='4h'):
    """Стратегия для бокового рынка: Bollinger Bands."""
    try:
        sma, upper_band, lower_band = await calculate_bollinger_bands(exchange, symbol, timeframe)
        if sma is None or upper_band is None or lower_band is None:
            return None

        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=1)
        if not ohlcv:
            return None
        current_price = ohlcv[-1][4]

        if current_price <= lower_band:
            return "buy"
        elif current_price >= upper_band:
            return "sell"
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to execute Bollinger Bands strategy for {symbol}: {type(e).__name__}: {str(e)}")
        return None

async def atr_cci_strategy(exchange, symbol, user, volatility, timeframe='4h'):
    """Стратегия для волатильного рынка: ATR + CCI."""
    try:
        cci = await calculate_cci(exchange, symbol, timeframe)
        if cci is None:
            return None

        cci_low, cci_high = await get_dynamic_thresholds("cci", volatility, user, symbol, base_low=-100, base_high=100)

        if cci < cci_low:
            return "buy"
        elif cci > cci_high:
            return "sell"
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to execute ATR+CCI strategy for {symbol}: {type(e).__name__}: {str(e)}")
        return None

async def select_strategy(exchange, symbol, user, market_state, volatility, timeframe='4h'):
    """Выбирает стратегию в зависимости от типа рынка."""
    market_type = market_state.get("market_type", "sideways")
    logger.info(f"Selecting strategy for {symbol}: market_type={market_type}")

    if market_type == "trending":
        return await rsi_sma_strategy(exchange, symbol, user, volatility, timeframe)
    elif market_type == "sideways":
        return await bollinger_strategy(exchange, symbol, user, volatility, timeframe)
    elif market_type == "volatile":
        return await atr_cci_strategy(exchange, symbol, user, volatility, timeframe)
    else:
        logger.warning(f"Unknown market type {market_type} for {symbol}, defaulting to no trade")
        return None
