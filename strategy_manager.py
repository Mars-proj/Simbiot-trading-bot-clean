# strategy_manager.py
import logging
import pandas as pd
import numpy as np
import redis.asyncio as redis
import json

logger = logging.getLogger("main")

async def get_redis_client():
    return await redis.from_url("redis://localhost:6379/0")

async def calculate_rsi(exchange, symbol, timeframe='4h', limit=100):
    """Рассчитывает RSI с кэшированием."""
    try:
        redis_client = await get_redis_client()
        rsi_key = f"rsi:{symbol}:{timeframe}"
        cached_rsi = await redis_client.get(rsi_key)
        if cached_rsi:
            return float(cached_rsi.decode())

        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < 14:
            logger.warning(f"Insufficient data to calculate RSI for {symbol}")
            return None
        closes = [candle[4] for candle in ohlcv]
        closes_series = pd.Series(closes)
        delta = closes_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_value = rsi.iloc[-1]

        await redis_client.set(rsi_key, str(rsi_value), ex=3600)  # Кэшируем на 1 час
        return rsi_value
    except Exception as e:
        logger.error(f"Failed to calculate RSI for {symbol}: {type(e).__name__}: {str(e)}")
        return None
    finally:
        await redis_client.close()

async def get_dynamic_thresholds(redis_client, symbol, market_state, volatility, success_rate):
    """Получает динамические пороговые значения RSI с учётом самообучения."""
    try:
        threshold_key = f"thresholds:{symbol}"
        threshold_data = await redis_client.get(threshold_key)
        if threshold_data:
            threshold_data = json.loads(threshold_data.decode())
            base_rsi_buy = threshold_data.get('rsi_buy', 30)
            base_rsi_sell = threshold_data.get('rsi_sell', 70)
        else:
            base_rsi_buy = 30
            base_rsi_sell = 70

        # Корректируем пороги на основе волатильности и состояния рынка
        if market_state == "bullish":
            base_rsi_buy -= 5 * volatility  # Более агрессивная покупка
            base_rsi_sell -= 5 * volatility  # Более ранняя продажа
        elif market_state == "bearish":
            base_rsi_buy += 5 * volatility  # Более осторожная покупка
            base_rsi_sell += 5 * volatility  # Более поздняя продажа

        # Корректируем пороги на основе успешности сделок
        if success_rate < 0.4:  # Если успешность низкая, делаем пороги более консервативными
            base_rsi_buy += 5
            base_rsi_sell -= 5
        elif success_rate > 0.6:  # Если успешность высокая, делаем пороги более агрессивными
            base_rsi_buy -= 5
            base_rsi_sell += 5

        # Ограничиваем пороги в разумных пределах
        base_rsi_buy = max(20, min(40, base_rsi_buy))
        base_rsi_sell = max(60, min(80, base_rsi_sell))

        # Сохраняем обновлённые пороги
        threshold_data = {'rsi_buy': base_rsi_buy, 'rsi_sell': base_rsi_sell}
        await redis_client.set(threshold_key, json.dumps(threshold_data), ex=86400 * 30)
        return base_rsi_buy, base_rsi_sell
    except Exception as e:
        logger.error(f"Failed to fetch dynamic thresholds for {symbol}: {type(e).__name__}: {str(e)}")
        return 30, 70
    finally:
        await redis_client.close()

async def select_strategy(exchange, symbol, user, market_state, volatility):
    redis_client = await get_redis_client()
    try:
        rsi = await calculate_rsi(exchange, symbol)
        if rsi is None:
            return None, None

        # Получаем историческую прибыльность для корректировки порогов
        profit_key = f"profitability:{symbol}"
        profit_data = await redis_client.get(profit_key)
        success_rate = 0.5
        if profit_data:
            profit_data = json.loads(profit_data.decode())
            success_rate = profit_data.get('success_rate', 0.5)

        rsi_buy, rsi_sell = await get_dynamic_thresholds(redis_client, symbol, market_state, volatility, success_rate)

        if rsi < rsi_buy:
            return "buy", f"RSI strategy (buy at RSI {rsi:.2f} < {rsi_buy:.2f})"
        elif rsi > rsi_sell:
            return "sell", f"RSI strategy (sell at RSI {rsi:.2f} > {rsi_sell:.2f})"
        return None, None
    except Exception as e:
        logger.error(f"Failed to select strategy for {symbol}: {type(e).__name__}: {str(e)}")
        return None, None
    finally:
        await redis_client.close()
