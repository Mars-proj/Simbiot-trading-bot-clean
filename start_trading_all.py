import logging
import time
import ccxt.async_support as ccxt
import pandas as pd
import numpy as np
import redis.asyncio as redis
import json
from ml_predictor import Predictor
from retraining_manager import RetrainingManager
from risk_manager import set_stop_loss, set_trailing_stop, calculate_exit_points
from notification_manager import NotificationManager
from features import calculate_volatility
from strategy_manager import StrategyManager
from genetic_optimizer import GeneticOptimizer

logger = logging.getLogger("main")

async def get_redis_client():
    """
    Initialize Redis client.

    Returns:
        Redis client instance.
    """
    return await redis.from_url("redis://localhost:6379/0")

async def save_position(user, symbol, trade):
    """
    Save position information to Redis.

    Args:
        user: User identifier.
        symbol: Trading symbol (e.g., 'BTC/USDT').
        trade: Trade details (dict).
    """
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
    """
    Retrieve position information from Redis.

    Args:
        user: User identifier.
        symbol: Trading symbol (e.g., 'BTC/USDT').

    Returns:
        dict: Position details, or None if not found.
    """
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
    """
    Delete position information from Redis.

    Args:
        user: User identifier.
        symbol: Trading symbol (e.g., 'BTC/USDT').
    """
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
    """
    Retrieve all open positions for a user from Redis.

    Args:
        user: User identifier.

    Returns:
        list: List of position details.
    """
    redis_client = await get_redis_client()
    try:
        positions = []
        keys = await redis_client.keys(f"positions:{user}:*")
        for key in keys:
            position_data = await redis_client.get(key)
            if position_data:
                position = json.loads(position_data.decode())
                if 'amount' in position and position['amount'] is not None:
                    positions.append(position)
                else:
                    symbol = key.decode().split(':')[-1]
                    logger.warning(f"Removing invalid position for {symbol} for user {user}: missing or invalid amount")
                    await redis_client.delete(key)
        return positions
    except Exception as e:
        logger.error(f"Failed to get all positions for user {user}: {type(e).__name__}: {str(e)}")
        return []
    finally:
        await redis_client.close()

async def calculate_profit(exchange, trade):
    """
    Calculate current profit/loss for a position.

    Args:
        exchange: Exchange instance (e.g., ccxt.async_support.mexc).
        trade: Trade details (dict).

    Returns:
        float: Profit/loss in USDT.
    """
    try:
        symbol = trade['symbol']
        amount = trade.get('amount')
        buy_price = trade.get('price')
        
        if amount is None or buy_price is None:
            logger.error(f"Invalid trade data for {symbol}: amount={amount}, buy_price={buy_price}")
            return 0
        
        ticker = await exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        profit = (current_price - buy_price) * amount
        fee_rate = 0.001  # Комиссия 0.1%
        fees = (buy_price * amount * fee_rate) + (current_price * amount * fee_rate)
        profit -= fees
        return profit
    except Exception as e:
        logger.error(f"Failed to calculate profit for {trade['symbol']}: {type(e).__name__}: {str(e)}")
        return 0

async def evaluate_trade(exchange, trade, symbol, user, market_state, notifier, strategy_manager):
    """
    Evaluate whether to close an open position based on RSI, profit, or holding time.

    Args:
        exchange: Exchange instance (e.g., ccxt.async_support.mexc).
        trade: Trade details (dict).
        symbol: Trading symbol (e.g., 'BTC/USDT').
        user: User identifier.
        market_state: Current market state (e.g., 'bullish', 'bearish').
        notifier: NotificationManager instance.
        strategy_manager: StrategyManager instance.

    Returns:
        tuple: (bool, float) - Whether to close the position, and the current profit/loss.
    """
    try:
        ticker = await exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        volatility = calculate_volatility(df)
        
        amount = trade.get('amount')
        buy_price = trade.get('price')
        cost = trade.get('cost', 0)
        
        if amount is None or buy_price is None:
            logger.error(f"Invalid trade data for {symbol}: amount={amount}, buy_price={buy_price}")
            return False, 0
        
        profit = (current_price - buy_price) * amount
        holding_time = (time.time() * 1000 - trade['timestamp']) / (1000 * 60 * 60)  # Время в часах
        
        exit_points = await calculate_exit_points(trade, current_price)
        take_profit = exit_points['take_profit']
        stop_loss = exit_points['stop_loss']
        
        if current_price >= take_profit or current_price <= stop_loss:
            logger.info(f"Closing position for {symbol}: profit={profit:.2f}, price={current_price}")
            await notifier.notify("user@example.com", f"Position Closed: {symbol}", f"Closed position for {symbol} with profit {profit:.2f}")
            strategy_manager.record_result(trade.get('strategy', 'unknown'), profit)
            return True, profit
        
        stop_loss_order = await set_stop_loss(exchange, symbol, amount, buy_price, volatility)
        if stop_loss_order:
            logger.info(f"Stop-loss triggered for {symbol}: {stop_loss_order}")
            await notifier.notify("user@example.com", f"Stop-Loss Triggered: {symbol}", f"Stop-loss triggered for {symbol}")
            strategy_manager.record_result(trade.get('strategy', 'unknown'), profit)
            return True, profit
        
        trailing_stop_order = await set_trailing_stop(exchange, symbol, amount, buy_price)
        if trailing_stop_order:
            logger.info(f"Trailing stop triggered for {symbol}: {trailing_stop_order}")
            await notifier.notify("user@example.com", f"Trailing Stop Triggered: {symbol}", f"Trailing stop triggered for {symbol}")
            strategy_manager.record_result(trade.get('strategy', 'unknown'), profit)
            return True, profit
        
        logger.debug(f"Evaluated trade for {symbol}: profit={profit:.2f}, holding_time={holding_time:.2f} hours")
        return False, profit
    except Exception as e:
        logger.error(f"Failed to evaluate trade for {symbol}: {type(e).__name__}: {str(e)}")
        return False, 0

async def optimize_thresholds(data, strategy_manager):
    """
    Optimize trading thresholds using genetic algorithms.

    Args:
        data (pd.DataFrame): OHLCV data.
        strategy_manager: StrategyManager instance.

    Returns:
        dict: Optimized thresholds.
    """
    def evaluate(individual):
        profit_target, stop_loss, trailing_percent = individual
        # Симуляция торговли с текущими порогами
        # Здесь нужно добавить логику симуляции, но для примера возвращаем случайное значение
        return random.uniform(-100, 100),

    optimizer = GeneticOptimizer(evaluate, [(0.01, 0.1), (0.01, 0.05), (0.005, 0.02)])
    best_params = optimizer.optimize()
    return {
        "profit_target": best_params[0],
        "stop_loss": best_params[1],
        "trailing_percent": best_params[2]
    }

async def start_trading_all(exchange, symbols, user, market_state):
    """
    Execute trading for a user with a list of symbols.

    - Evaluates and closes existing positions if necessary.
    - Opens new positions based on trading signals.

    Args:
        exchange: Exchange instance (e.g., ccxt.async_support.mexc).
        symbols: List of symbols to trade.
        user: User identifier.
        market_state: Current market state (e.g., 'bullish', 'bearish').

    Returns:
        int: Number of trading signals processed.
    """
    signal_count = 0
    notifier = NotificationManager()
    strategy_manager = StrategyManager()
    retraining_manager = RetrainingManager()
    predictor = Predictor(retraining_manager)
    
    positions = await get_all_positions(user)
    logger.info(f"User {user} has {len(positions)} open positions")
    
    if len(positions) >= 5:  # MAX_OPEN_POSITIONS
        logger.warning(f"User {user} has reached max open positions (5)")
        return signal_count
    
    positions_with_profit = []
    usdt_balance = 0
    for position in positions:
        should_close, profit = await evaluate_trade(exchange, position, position['symbol'], user, market_state, notifier, strategy_manager)
        if should_close:
            try:
                symbol = position['symbol']
                base_currency = symbol.split('/')[0]
                balance = await exchange.fetch_balance()
                available_amount = balance.get(base_currency, {}).get('free', 0)
                
                if available_amount <= 0:
                    logger.warning(f"Cannot close position for {symbol}: no available {base_currency} to sell")
                    await delete_position(user, symbol)
                    continue
                
                amount_to_sell = min(position['amount'], available_amount)
                if amount_to_sell <= 0:
                    logger.warning(f"Cannot close position for {symbol}: amount to sell is zero or negative ({amount_to_sell})")
                    await delete_position(user, symbol)
                    continue
                
                sell_order = await exchange.create_market_sell_order(symbol, amount_to_sell)
                logger.info(f"Sell trade executed for {symbol} on {exchange.id}: {sell_order}")
                await delete_position(user, symbol)
                balance = await exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                logger.info(f"Updated USDT balance after selling {symbol}: {usdt_balance}")
            except Exception as e:
                logger.error(f"Failed to close position for {symbol}: {type(e).__name__}: {str(e)}")
                if "InsufficientFunds" in str(e):
                    logger.warning(f"Removing position for {symbol} due to insufficient funds")
                    await delete_position(user, symbol)
        else:
            positions_with_profit.append((position, profit))
    
    if usdt_balance < 10:
        if positions_with_profit:
            logger.warning(f"Insufficient USDT balance for {user}: {usdt_balance}, waiting for positions to close")
            return signal_count
        else:
            logger.warning(f"Insufficient USDT balance for {user}: {usdt_balance}, no positions to sell")
            return signal_count
    
    positions_with_profit.sort(key=lambda x: x[1], reverse=True)
    
    for symbol in symbols:
        balance = await exchange.fetch_balance()
        usdt_balance = balance.get('USDT', {}).get('free', 0)
        if usdt_balance < 10:
            if positions_with_profit:
                least_profitable_position, least_profit = positions_with_profit[-1]
                try:
                    least_symbol = least_profitable_position['symbol']
                    base_currency = least_symbol.split('/')[0]
                    balance = await exchange.fetch_balance()
                    available_amount = balance.get(base_currency, {}).get('free', 0)
                    
                    if available_amount <= 0:
                        logger.warning(f"Cannot close position for {least_symbol}: no available {base_currency} to sell")
                        await delete_position(user, least_symbol)
                        positions_with_profit.pop()
                        continue
                    
                    amount_to_sell = min(least_profitable_position['amount'], available_amount)
                    if amount_to_sell <= 0:
                        logger.warning(f"Cannot close position for {least_symbol}: amount to sell is zero or negative ({amount_to_sell})")
                        await delete_position(user, least_symbol)
                        positions_with_profit.pop()
                        continue
                    
                    sell_order = await exchange.create_market_sell_order(least_symbol, amount_to_sell)
                    logger.info(f"Sell trade executed for {least_symbol} to free up funds: {sell_order}")
                    await delete_position(user, least_symbol)
                    balance = await exchange.fetch_balance()
                    usdt_balance = balance.get('USDT', {}).get('free', 0)
                    logger.info(f"Updated USDT balance after selling {least_symbol}: {usdt_balance}")
                    positions_with_profit.pop()
                except Exception as e:
                    logger.error(f"Failed to sell {least_symbol}: {type(e).__name__}: {str(e)}")
                    if "InsufficientFunds" in str(e):
                        logger.warning(f"Removing position for {least_symbol} due to insufficient funds")
                        await delete_position(user, least_symbol)
                        positions_with_profit.pop()
                    continue
            else:
                logger.warning(f"Insufficient USDT balance for {user}: {usdt_balance}, no positions to sell")
                break
        
        try:
            existing_position = await get_position(user, symbol)
            if existing_position:
                continue
            
            ohlcv = await exchange.fetch_ohlcv(symbol, '1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            signal = await predictor.predict_signal(symbol, df, model_type="lstm")
            if signal not in ["buy", "sell"]:
                raise ValueError(f"Invalid signal: {signal}")
            
            strategy_name, ab_signal = strategy_manager.ab_test(df)
            if ab_signal != signal:
                signal = ab_signal
            
            current_price = df['close'].iloc[-1]
            if current_price <= 0:
                logger.warning(f"Skipping {symbol}: current price is zero or negative ({current_price})")
                continue
            
            balance = await exchange.fetch_balance()
            usdt_balance = balance.get('USDT', {}).get('free', 0)
            if usdt_balance < 10:
                logger.warning(f"Still insufficient USDT balance for {user}: {usdt_balance}")
                break
            
            amount_usd = max(10, usdt_balance * 0.1)  # MIN_TRADE_AMOUNT_USD, MAX_POSITION_PERCENTAGE
            amount = amount_usd / current_price
            
            market = exchange.markets[symbol]
            min_amount = market.get('limits', {}).get('amount', {}).get('min', 0)
            if min_amount and amount < min_amount:
                logger.warning(f"Skipping {symbol}: calculated amount {amount} is less than minimum {min_amount}")
                continue
            
            if amount <= 0:
                logger.warning(f"Skipping {symbol}: calculated amount is zero or negative ({amount})")
                continue
            
            if signal == "buy":
                trade = await exchange.create_market_buy_order(symbol, amount)
                trade['strategy'] = strategy_name  # Сохраняем стратегию для A/B-тестирования
                logger.info(f"Buy trade executed for {symbol} on {exchange.id}: {trade}")
                await save_position(user, symbol, trade)
                await notifier.notify("user@example.com", f"New Position: {symbol}", f"Opened position for {symbol} at {current_price}")
                balance = await exchange.fetch_balance()
                usdt_balance = balance.get('USDT', {}).get('free', 0)
                logger.info(f"Updated USDT balance after buying {symbol}: {usdt_balance}")
                signal_count += 1
        except Exception as e:
            logger.error(f"Failed to process {symbol}: {type(e).__name__}: {str(e)}")
            continue
    
    return signal_count
