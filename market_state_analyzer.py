# market_state_analyzer.py
import logging
import pandas as pd
import numpy as np
import redis.asyncio as redis
import json

logger = logging.getLogger("main")

async def get_redis_client():
    return await redis.from_url("redis://localhost:6379/0")

async def analyze_market_state(exchange, symbol, timeframe='4h', limit=100):
    """Анализирует состояние рынка с учётом самообучения."""
    try:
        redis_client = await get_redis_client()
        state_key = f"market_state:{symbol}:{timeframe}"
        cached_state = await redis_client.get(state_key)
        if cached_state:
            return cached_state.decode()

        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < 20:
            logger.warning(f"Insufficient data to analyze market state for {symbol}")
            return "neutral"

        closes = [candle[4] for candle in ohlcv]
        closes_series = pd.Series(closes)

        # Рассчитываем скользящие средние
        sma_short = closes_series.rolling(window=5).mean().iloc[-1]
        sma_long = closes_series.rolling(window=20).mean().iloc[-1]

        # Определяем тренд
        if sma_short > sma_long:
            state = "bullish"
        elif sma_short < sma_long:
            state = "bearish"
        else:
            state = "neutral"

        # Корректируем состояние на основе исторической успешности
        profit_key = f"profitability:{symbol}"
        profit_data = await redis_client.get(profit_key)
        if profit_data:
            profit_data = json.loads(profit_data.decode())
            success_rate = profit_data.get('success_rate', 0.5)
            if success_rate < 0.4 and state == "bullish":
                state = "neutral"  # Если успешность низкая, не доверяем бычьему тренду
            elif success_rate > 0.6 and state == "bearish":
                state = "neutral"  # Если успешность высокая, не доверяем медвежьему тренду

        await redis_client.set(state_key, state, ex=3600)  # Кэшируем на 1 час
        return state
    except Exception as e:
        logger.error(f"Failed to analyze market state for {symbol}: {type(e).__name__}: {str(e)}")
        return "neutral"
    finally:
        await redis_client.close()
