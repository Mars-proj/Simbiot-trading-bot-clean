import logging
import pandas as pd
import redis.asyncio as redis
import json
import numpy as np

logger = logging.getLogger("main")

async def get_redis_client():
    return await redis.from_url("redis://localhost:6379/0")

async def analyze_market_state(exchange, symbol, timeframe='1h', limit=100):
    """
    Analyze market state based on multiple indicators with Redis caching.

    Args:
        exchange: Exchange instance (e.g., ccxt.async_support.mexc).
        symbol: Symbol to analyze (e.g., 'BTC/USDT').
        timeframe: Timeframe for OHLCV data (default: '1h').
        limit: Number of OHLCV candles to fetch (default: 100).

    Returns:
        dict: Market state with indicators.
    """
    cache_key = f"market_state:{symbol}:{timeframe}"
    redis_client = await get_redis_client()
    try:
        cached_state = await redis_client.get(cache_key)
        if cached_state:
            return json.loads(cached_state.decode())
    except Exception as e:
        logger.error(f"Failed to check cache for market state: {type(e).__name__}: {str(e)}")
    finally:
        await redis_client.close()

    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # SMA
        df['sma_20'] = df['close'].rolling(window=20).mean()
        trend = "bullish" if df['close'].iloc[-1] > df['sma_20'].iloc[-1] else "bearish"

        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_trend = "bullish" if macd.iloc[-1] > signal_line.iloc[-1] else "bearish"

        # Bollinger Bands
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['std_20'] = df['close'].rolling(window=20).std()
        df['upper_band'] = df['sma_20'] + (df['std_20'] * 2)
        df['lower_band'] = df['sma_20'] - (df['std_20'] * 2)
        bb_position = "overbought" if df['close'].iloc[-1] > df['upper_band'].iloc[-1] else "oversold" if df['close'].iloc[-1] < df['lower_band'].iloc[-1] else "neutral"

        state = {
            "trend": trend,
            "macd_trend": macd_trend,
            "bb_position": bb_position,
            "macd": macd.iloc[-1],
            "signal_line": signal_line.iloc[-1],
            "upper_band": df['upper_band'].iloc[-1],
            "lower_band": df['lower_band'].iloc[-1]
        }

        # Сохраняем в кэш
        redis_client = await get_redis_client()
        try:
            await redis_client.set(cache_key, json.dumps(state), ex=3600)  # Кэшируем на 1 час
        except Exception as e:
            logger.error(f"Failed to cache market state: {type(e).__name__}: {str(e)}")
        finally:
            await redis_client.close()

        return state
    except Exception as e:
        logger.error(f"Failed to analyze market state for {symbol}: {type(e).__name__}: {str(e)}")
        return {"trend": "unknown", "macd_trend": "unknown", "bb_position": "unknown"}
