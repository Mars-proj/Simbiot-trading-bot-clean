# start_trading_all.py
import logging
import numpy as np
import pandas as pd
import redis.asyncio as redis
import json
from datetime import datetime

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

async def calculate_volatility(exchange, symbol, timeframe='4h', limit=100):
    """Вычисляет волатильность символа (стандартное отклонение цен)."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < 2:
            logger.warning(f"Insufficient data to calculate volatility for {symbol}")
            return 0.01

        closes = [candle[4] for candle in ohlcv]
        returns = pd.Series(closes).pct_change().dropna()
        volatility = returns.std() * np.sqrt(24 * 365)
        return volatility if not np.isnan(volatility) else 0.01
    except Exception as e:
        logger.error(f"Failed to calculate volatility for {symbol}: {type(e).__name__}: {str(e)}")
        return 0.01

async def calculate_average_volume(exchange, symbol, timeframe='4h', limit=100):
    """Вычисляет средний дневной объём торгов."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < 2:
            logger.warning(f"Insufficient data to calculate average volume for {symbol}")
            return 0

        volumes = [candle[5] for candle in ohlcv]
        avg_volume = np.mean(volumes)
        return avg_volume if not np.isnan(avg_volume) else 0
    except Exception as e:
        logger.error(f"Failed to calculate average volume for {symbol}: {type(e).__name__}: {str(e)}")
        return 0

async def get_dynamic_rsi_thresholds(symbol, volatility, user):
    """Вычисляет динамические пороговые значения RSI."""
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

        base_rsi_buy = 40
        base_rsi_sell = 60

        volatility_factor = 1 + (volatility / 10)
        success_factor = 1 - (success_rate - 0.5)

        rsi_buy = base_rsi_buy * success_factor / volatility_factor
        rsi_sell = base_rsi_sell * success_factor * volatility_factor

        rsi_buy = max(30, min(45, rsi_buy))
        rsi_sell = max(55, min(70, rsi_sell))

        return rsi_buy, rsi_sell
    finally:
        await redis_client.close()

async def calculate_order_amount(exchange, symbol, volatility, avg_volume):
    """Вычисляет динамический объём ордера в долларах."""
    try:
        ticker = await exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        if not current_price or current_price <= 0:
            logger.warning(f"Invalid price for {symbol}: {current_price}")
            return 0

        min_amount_usd = 10
        max_amount_usd = (avg_volume * current_price * 0.001) * (1 + volatility)
        max_amount_usd = max(min_amount_usd, min(max_amount_usd, 1000))

        amount_usd = max(min_amount_usd, max_amount_usd * 0.5)
        amount = amount_usd / current_price
        return amount
    except Exception as e:
        logger.error(f"Failed to calculate order amount for {symbol}: {type(e).__name__}: {str(e)}")
        return 0

async def update_trade_success(symbol, user, profit):
    """Обновляет статистику успешности сделок в Redis."""
    redis_client = await get_redis_client()
    try:
        success_key = f"trade_success:{symbol}:{user}"
        success_data = await redis_client.get(success_key)
        if success_data:
            success_data = json.loads(success_data.decode())
        else:
            success_data = {'total_trades': 0, 'successful_trades': 0}

        success_data['total_trades'] += 1
        if profit > 0:
            success_data['successful_trades'] += 1

        await redis_client.set(success_key, json.dumps(success_data), ex=86400 * 30)
    finally:
        await redis_client.close()

async def start_trading_all(exchange, valid_symbols, user):
    logger.debug(f"Exchange instance received: {exchange}")
    logger.debug(f"Exchange methods available: {dir(exchange)}")
    logger.info(f"Starting trading for user {user} with {len(valid_symbols)} symbols: {valid_symbols}")

    signal_count = 0
    for symbol in valid_symbols:
        try:
            rsi = await calculate_rsi(exchange, symbol)
            if rsi is None:
                logger.warning(f"Skipping {symbol} due to insufficient RSI data")
                continue

            short_sma, long_sma = await calculate_sma(exchange, symbol)
            if short_sma is None or long_sma is None:
                logger.warning(f"Skipping {symbol} due to insufficient SMA data")
                continue

            volatility = await calculate_volatility(exchange, symbol)
            avg_volume = await calculate_average_volume(exchange, symbol)

            rsi_buy, rsi_sell = await get_dynamic_rsi_thresholds(symbol, volatility, user)
            logger.info(f"RSI for {symbol}: {rsi}, thresholds: buy={rsi_buy}, sell={rsi_sell}, volatility={volatility}, avg_volume={avg_volume}")
            logger.info(f"SMA for {symbol}: short={short_sma}, long={long_sma}")

            if rsi < rsi_buy and short_sma > long_sma:
                amount = await calculate_order_amount(exchange, symbol, volatility, avg_volume)
                if amount <= 0:
                    logger.warning(f"Skipping buy for {symbol}: invalid order amount {amount}")
                    continue

                logger.debug(f"Placing market buy order for {symbol} with amount {amount} (RSI: {rsi}, SMA: short={short_sma}, long={long_sma})")
                order = await exchange.create_market_buy_order(symbol, amount)
                logger.info(f"Buy trade executed for {symbol} on mexc: {order}")
                logger.info(f"Order details: id={order.get('id')}, status={order.get('status')}, filled={order.get('filled')}")

                await update_trade_success(symbol, user, 0)
                signal_count += 1

            elif rsi > rsi_sell and short_sma < long_sma:
                amount = await calculate_order_amount(exchange, symbol, volatility, avg_volume)
                if amount <= 0:
                    logger.warning(f"Skipping sell for {symbol}: invalid order amount {amount}")
                    continue

                logger.debug(f"Placing market sell order for {symbol} with amount {amount} (RSI: {rsi}, SMA: short={short_sma}, long={long_sma})")
                order = await exchange.create_market_sell_order(symbol, amount)
                logger.info(f"Sell trade executed for {symbol} on mexc: {order}")
                logger.info(f"Order details: id={order.get('id')}, status={order.get('status')}, filled={order.get('filled')}")

                await update_trade_success(symbol, user, 0)
                signal_count += 1

            else:
                logger.debug(f"No trade for {symbol}: RSI {rsi}, SMA: short={short_sma}, long={long_sma}")
        except Exception as e:
            logger.error(f"Failed to process {symbol}: {type(e).__name__}: {str(e)}")
    return signal_count
