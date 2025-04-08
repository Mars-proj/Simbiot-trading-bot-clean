# start_trading_all.py
import logging
import redis.asyncio as redis
import numpy as np
import pandas as pd
import json
from strategy_manager import select_strategy
from learning.trade_evaluator import evaluate_trade

logger = logging.getLogger("main")

async def get_redis_client():
    """Инициализация Redis клиента."""
    return await redis.from_url("redis://localhost:6379/0")

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

async def manage_position(exchange, symbol, user, signal, amount, current_price):
    """Управляет позицией: открывает или закрывает позицию и возвращает прибыль."""
    redis_client = await get_redis_client()
    try:
        position_key = f"position:{symbol}:{user}"
        position_data = await redis_client.get(position_key)
        if position_data:
            position_data = json.loads(position_data.decode())
        else:
            position_data = {'amount': 0, 'entry_price': 0}

        profit = 0
        if signal == "buy":
            # Open or add to position
            if position_data['amount'] > 0:
                # Average the entry price
                total_amount = position_data['amount'] + amount
                total_cost = (position_data['amount'] * position_data['entry_price']) + (amount * current_price)
                position_data['entry_price'] = total_cost / total_amount
                position_data['amount'] = total_amount
            else:
                position_data['amount'] = amount
                position_data['entry_price'] = current_price
        elif signal == "sell":
            if position_data['amount'] > 0:
                # Close position and calculate profit
                profit = (current_price - position_data['entry_price']) * min(amount, position_data['amount'])
                position_data['amount'] -= amount
                if position_data['amount'] <= 0:
                    position_data['amount'] = 0
                    position_data['entry_price'] = 0
            else:
                logger.warning(f"No position to sell for {symbol}")
                return 0

        await redis_client.set(position_key, json.dumps(position_data), ex=86400 * 30)
        return profit
    except Exception as e:
        logger.error(f"Failed to manage position for {symbol}: {type(e).__name__}: {str(e)}")
        return 0
    finally:
        await redis_client.close()

async def start_trading_all(exchange, valid_symbols, user, market_state):
    logger.debug(f"Exchange instance received: {exchange}")
    logger.debug(f"Exchange methods available: {dir(exchange)}")
    logger.info(f"Starting trading for user {user} with {len(valid_symbols)} symbols: {valid_symbols}")

    signal_count = 0
    for symbol in valid_symbols:
        try:
            volatility = await calculate_volatility(exchange, symbol)
            avg_volume = await calculate_average_volume(exchange, symbol)

            # Select strategy based on market type
            signal, strategy_info = await select_strategy(exchange, symbol, user, market_state, volatility)
            if signal is None:
                logger.debug(f"No trade for {symbol}: No signal generated")
                continue

            amount = await calculate_order_amount(exchange, symbol, volatility, avg_volume)
            if amount <= 0:
                logger.warning(f"Skipping trade for {symbol}: invalid order amount {amount}")
                continue

            # Get current price for profit calculation
            ticker = await exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            if not current_price or current_price <= 0:
                logger.warning(f"Invalid price for {symbol}: {current_price}")
                continue

            # Manage position and calculate profit
            profit = await manage_position(exchange, symbol, user, signal, amount, current_price)

            if signal == "buy":
                logger.debug(f"Placing market buy order for {symbol} with amount {amount}")
                order = await exchange.create_market_buy_order(symbol, amount)
                logger.info(f"Buy trade executed for {symbol} on mexc: {order}")
                logger.info(f"Order details: id={order.get('id')}, status={order.get('status')}, filled={order.get('filled')}")
                signal_count += 1
                await evaluate_trade(symbol, user, strategy_info, profit)
            elif signal == "sell":
                logger.debug(f"Placing market sell order for {symbol} with amount {amount}")
                order = await exchange.create_market_sell_order(symbol, amount)
                logger.info(f"Sell trade executed for {symbol} on mexc: {order}")
                logger.info(f"Order details: id={order.get('id')}, status={order.get('status')}, filled={order.get('filled')}")
                signal_count += 1
                await evaluate_trade(symbol, user, strategy_info, profit)
        except Exception as e:
            logger.error(f"Failed to process {symbol}: {type(e).__name__}: {str(e)}")
    return signal_count
