# start_trading_all.py
import logging
import redis.asyncio as redis
import numpy as np
import pandas as pd
import json
import asyncio
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

async def get_historical_profitability(redis_client, symbol):
    """Получает историческую прибыльность сделок по символу из Redis."""
    try:
        profit_key = f"profitability:{symbol}"
        profit_data = await redis_client.get(profit_key)
        if profit_data:
            profit_data = json.loads(profit_data.decode())
            return profit_data.get('success_rate', 0.5)  # По умолчанию 50% успеха
        return 0.5  # Если данных нет, считаем сигнал нейтральным
    except Exception as e:
        logger.error(f"Failed to fetch profitability for {symbol}: {type(e).__name__}: {str(e)}")
        return 0.5

async def check_balance(exchange, user, min_amount_usd):
    """Проверяет доступный баланс USDT на счету."""
    try:
        balance = await exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        logger.debug(f"Available USDT balance for {user}: {usdt_balance}")
        return usdt_balance, usdt_balance >= min_amount_usd
    except Exception as e:
        logger.error(f"Failed to fetch balance for {user}: {type(e).__name__}: {str(e)}")
        return 0, False

async def calculate_order_amount(exchange, symbol, volatility, avg_volume, signal_strength, min_notional=10.0, commission_rate=0.001):
    """Вычисляет динамический объём ордера в базовой валюте с учётом минимального значения и комиссии."""
    try:
        # Получаем текущую цену символа
        ticker = await exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        if not current_price or current_price <= 0:
            logger.warning(f"Invalid price for {symbol}: {current_price}")
            return 0

        # Получаем баланс
        balance, _ = await check_balance(exchange, "user", min_notional * (1 + commission_rate))
        if balance <= 0:
            logger.warning(f"No available balance for {symbol}")
            return 0

        # Минимальная сумма в USDT (10 долларов + комиссия)
        min_amount_usd = min_notional * (1 + commission_rate)

        # Динамическая максимальная сумма на основе баланса (не более 10% от депозита)
        max_amount_usd = balance * 0.1  # Ограничиваем 10% от депозита

        # Базовая сумма на основе объёма торгов и волатильности
        base_amount_usd = (avg_volume * current_price * 0.001) * (1 + volatility)

        # Корректируем сумму на основе силы сигнала (signal_strength от 0 до 1)
        adjusted_amount_usd = base_amount_usd * signal_strength

        # Ограничиваем сумму в диапазоне от min_amount_usd до max_amount_usd
        amount_usd = max(min_amount_usd, min(adjusted_amount_usd, max_amount_usd))

        # Рассчитываем количество базовой валюты (например, BTC для BTC/USDT)
        amount = amount_usd / current_price

        # Получаем информацию о рынке для проверки минимального количества
        market = exchange.markets[symbol]
        min_amount = market.get('limits', {}).get('amount', {}).get('min', 0.0)
        if amount < min_amount:
            logger.warning(f"Calculated amount {amount} for {symbol} is below minimum {min_amount}, adjusting to minimum")
            amount = min_amount

        # Проверяем, что итоговая сумма в USDT не меньше минимальной
        final_amount_usd = amount * current_price
        if final_amount_usd < min_amount_usd:
            logger.warning(f"Final amount {final_amount_usd} USD for {symbol} is below minimum {min_amount_usd}, adjusting")
            amount = min_amount_usd / current_price

        logger.debug(f"Calculated order amount for {symbol}: {amount} (price: {current_price}, amount_usd: {amount * current_price}, signal_strength: {signal_strength})")
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
    min_notional = 10.0  # Минимальная сумма ордера в USDT
    commission_rate = 0.001  # Комиссия 0.1%
    redis_client = await get_redis_client()

    try:
        for symbol in valid_symbols:
            try:
                # Проверяем баланс перед открытием сделки
                balance, has_enough_balance = await check_balance(exchange, user, min_notional * (1 + commission_rate))
                if not has_enough_balance:
                    logger.warning(f"Insufficient USDT balance for {user} ({balance} USDT), waiting for funds...")
                    await asyncio.sleep(60)  # Ждём 60 секунд перед следующей проверкой
                    continue

                volatility = await calculate_volatility(exchange, symbol)
                avg_volume = await calculate_average_volume(exchange, symbol)
                # Select strategy based on market type
                signal, strategy_info = await select_strategy(exchange, symbol, user, market_state, volatility)
                if signal is None:
                    logger.debug(f"No trade for {symbol}: No signal generated")
                    continue

                # Получаем историческую прибыльность для символа
                signal_strength = await get_historical_profitability(redis_client, symbol)

                amount = await calculate_order_amount(exchange, symbol, volatility, avg_volume, signal_strength, min_notional, commission_rate)
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

                # Добавляем задержку, чтобы избежать превышения лимита запросов
                await asyncio.sleep(0.5)  # Задержка 0.5 секунды между запросами
            except Exception as e:
                logger.error(f"Failed to process {symbol}: {type(e).__name__}: {str(e)}")
                if "Too Many Requests" in str(e):
                    logger.warning(f"Rate limit exceeded, pausing for 5 seconds...")
                    await asyncio.sleep(5)  # Задержка 5 секунд при превышении лимита
    finally:
        await redis_client.close()
    return signal_count
