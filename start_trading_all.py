# start_trading_all.py
import logging
import time
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import redis.asyncio as redis
import json

logger = logging.getLogger("main")

async def get_redis_client():
    """Инициализация Redis клиента."""
    return await redis.from_url("redis://localhost:6379/0")

async def save_position(user, symbol, trade):
    """Сохраняет информацию об открытой позиции в Redis."""
    redis_client = await get_redis_client()
    try:
        position_key = f"positions:{user}:{symbol}"
        await redis_client.set(position_key, json.dumps(trade), ex=86400)  # Храним 24 часа
        logger.debug(f"Saved position for {symbol} for user {user}")
    except Exception as e:
        logger.error(f"Failed to save position for {symbol}: {type(e).__name__}: {str(e)}")
    finally:
        await redis_client.close()

async def get_position(user, symbol):
    """Получает информацию об открытой позиции из Redis."""
    redis_client = await get_redis_client()
    try:
        position_key = f"positions:{user}:{symbol}"
        position_data = await redis_client.get(position_key)
        if position_data:
            return json.loads(position_data.decode())
        return None
    except Exception as e:
        logger.error(f"Failed to get position for {symbol}: {type(e).__name__}: {str(e)}")
        return None
    finally:
        await redis_client.close()

async def delete_position(user, symbol):
    """Удаляет информацию об открытой позиции из Redis."""
    redis_client = await get_redis_client()
    try:
        position_key = f"positions:{user}:{symbol}"
        await redis_client.delete(position_key)
        logger.debug(f"Deleted position for {symbol} for user {user}")
    except Exception as e:
        logger.error(f"Failed to delete position for {symbol}: {type(e).__name__}: {str(e)}")
    finally:
        await redis_client.close()

async def get_all_positions(user):
    """Получает все открытые позиции пользователя из Redis."""
    redis_client = await get_redis_client()
    try:
        positions = []
        keys = await redis_client.keys(f"positions:{user}:*")
        for key in keys:
            position_data = await redis_client.get(key)
            if position_data:
                positions.append(json.loads(position_data.decode()))
        return positions
    except Exception as e:
        logger.error(f"Failed to get all positions for user {user}: {type(e).__name__}: {str(e)}")
        return []
    finally:
        await redis_client.close()

async def calculate_profit(exchange, trade):
    """Рассчитывает текущую прибыль/убыток по позиции."""
    try:
        symbol = trade['symbol']
        amount = trade['amount']
        buy_price = trade['price']
        
        ticker = await exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        profit = (current_price - buy_price) * amount
        return profit
    except Exception as e:
        logger.error(f"Failed to calculate profit for {trade['symbol']}: {type(e).__name__}: {str(e)}")
        return 0

async def evaluate_trade(exchange, trade, symbol, user, market_state):
    try:
        # Получаем текущую цену
        ticker = await exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Получаем данные OHLCV для анализа
        ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Вычисляем RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Логика оценки
        profit = (current_price - trade['price']) * trade['amount']
        holding_time = (time.time() * 1000 - trade['timestamp']) / (1000 * 60 * 60)  # Время в часах
        
        logger.debug(f"Evaluated trade for {symbol}: profit={profit:.2f}, RSI={current_rsi:.2f}, holding_time={holding_time:.2f} hours")
        
        # Простая логика закрытия позиции
        if current_rsi > 70 or profit > 0.05 * trade['cost'] or holding_time > 24:
            logger.info(f"Closing position for {symbol}: profit={profit:.2f}, RSI={current_rsi:.2f}")
            return True, profit
        return False, profit
    except Exception as e:
        logger.error(f"Failed to evaluate trade for {symbol}: {type(e).__name__}: {str(e)}")
        return False, 0

async def evaluate_potential_trade(exchange, symbol, timeframe='1h', limit=100):
    """Оценивает потенциальную прибыльность нового символа."""
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df['sma_20'] = df['close'].rolling(window=20).mean()
        current_price = df['close'].iloc[-1]
        sma_20 = df['sma_20'].iloc[-1]
        
        # Простая метрика прибыльности: если цена выше SMA и тренд растущий
        if current_price > sma_20:
            # Оцениваем потенциальную прибыль на основе последних 20 свечей
            recent_returns = df['close'].pct_change().tail(20).mean() * 100  # Средняя доходность в %
            return recent_returns
        return 0
    except Exception as e:
        logger.error(f"Failed to evaluate potential trade for {symbol}: {type(e).__name__}: {str(e)}")
        return 0

async def start_trading_all(exchange, symbols, user, market_state):
    signal_count = 0
    
    # Получаем все открытые позиции
    positions = await get_all_positions(user)
    logger.info(f"User {user} has {len(positions)} open positions")
    
    # Оцениваем текущие позиции
    positions_with_profit = []
    usdt_balance = 0
    for position in positions:
        should_close, profit = await evaluate_trade(exchange, position, position['symbol'], user, market_state)
        if should_close:
            try:
                # Закрываем позицию
                sell_order = await exchange.create_market_sell_order(position['symbol'], position['amount'])
                logger.info(f"Sell trade executed for {position['symbol']} on {exchange.id}: {sell_order}")
                await delete_position(user, position['symbol'])
                # Обновляем баланс на основе реальной суммы продажи
                balance = await exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                logger.info(f"Updated USDT balance after selling {position['symbol']}: {usdt_balance}")
            except Exception as e:
                logger.error(f"Failed to close position for {position['symbol']}: {type(e).__name__}: {str(e)}")
        else:
            positions_with_profit.append((position, profit))
    
    # Проверяем баланс после закрытия позиций
    if usdt_balance < 10:
        # Если баланса недостаточно, но есть позиции, ждём их закрытия
        if positions_with_profit:
            logger.warning(f"Insufficient USDT balance for {user}: {usdt_balance}, waiting for positions to close")
            return signal_count
        else:
            logger.warning(f"Insufficient USDT balance for {user}: {usdt_balance}, no positions to sell")
            return signal_count
    
    # Сортируем позиции по прибыльности (по убыванию)
    positions_with_profit.sort(key=lambda x: x[1], reverse=True)
    
    for symbol in symbols:
        try:
            # Проверяем, есть ли уже открытая позиция для этого символа
            existing_position = await get_position(user, symbol)
            if existing_position:
                continue  # Пропускаем символ, если позиция уже открыта
            
            # Получаем данные OHLCV
            ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Простая торговая стратегия: покупаем, если цена выше 20-периодной SMA
            df['sma_20'] = df['close'].rolling(window=20).mean()
            current_price = df['close'].iloc[-1]
            sma_20 = df['sma_20'].iloc[-1]
            
            # Оцениваем потенциальную прибыльность
            potential_profit = await evaluate_potential_trade(exchange, symbol)
            
            # Проверяем, стоит ли открывать новую позицию
            if current_price > sma_20:
                # Проверяем, что цена не нулевая
                if current_price <= 0:
                    logger.warning(f"Skipping {symbol}: current price is zero or negative ({current_price})")
                    continue
                
                # Проверяем баланс перед каждой сделкой
                balance = await exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                if usdt_balance < 10:
                    # Если баланса недостаточно, проверяем, можем ли продать менее прибыльную позицию
                    if positions_with_profit:
                        least_profitable_position, least_profit = positions_with_profit[-1]
                        if potential_profit > least_profit:
                            # Продаём менее прибыльную позицию
                            try:
                                sell_order = await exchange.create_market_sell_order(least_profitable_position['symbol'], least_profitable_position['amount'])
                                logger.info(f"Sell trade executed for {least_profitable_position['symbol']} to free up funds: {sell_order}")
                                await delete_position(user, least_profitable_position['symbol'])
                                # Обновляем баланс после продажи
                                balance = await exchange.fetch_balance()
                                usdt_balance = balance.get('USDT', {}).get('free', 0)
                                logger.info(f"Updated USDT balance after selling {least_profitable_position['symbol']}: {usdt_balance}")
                                positions_with_profit.pop()  # Удаляем проданную позицию
                            except Exception as e:
                                logger.error(f"Failed to sell {least_profitable_position['symbol']}: {type(e).__name__}: {str(e)}")
                                continue
                    else:
                        logger.warning(f"Insufficient USDT balance for {user}: {usdt_balance}, no positions to sell")
                        continue
                
                # Проверяем баланс снова
                if usdt_balance < 10:
                    logger.warning(f"Still insufficient USDT balance for {user}: {usdt_balance}")
                    continue
                
                # Рассчитываем сумму ордера (10% от баланса, но не менее 10 USDT)
                amount_usd = max(10, usdt_balance * 0.1)
                amount = amount_usd / current_price
                
                # Проверяем минимальное количество токенов
                market = exchange.markets[symbol]
                min_amount = market.get('limits', {}).get('amount', {}).get('min', 0)
                if min_amount and amount < min_amount:
                    logger.warning(f"Skipping {symbol}: calculated amount {amount} is less than minimum {min_amount}")
                    continue
                
                # Проверяем, что количество положительное и не равно нулю
                if amount <= 0:
                    logger.warning(f"Skipping {symbol}: calculated amount is zero or negative ({amount})")
                    continue
                
                # Создаём ордер
                trade = await exchange.create_market_buy_order(symbol, amount)
                logger.info(f"Buy trade executed for {symbol} on {exchange.id}: {trade}")
                logger.info(f"Order details: id={trade['id']}, status={trade['status']}, filled={trade['filled']}")
                
                # Сохраняем информацию об открытой позиции
                await save_position(user, symbol, trade)
                
                # Обновляем баланс
                balance = await exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                logger.info(f"Updated USDT balance after buying {symbol}: {usdt_balance}")
                
                signal_count += 1
        except Exception as e:
            logger.error(f"Failed to process {symbol}: {type(e).__name__}: {str(e)}")
            continue
    return signal_count
