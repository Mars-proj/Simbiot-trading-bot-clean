import asyncio
import pandas as pd
from logging_setup import logger_main, logger_exceptions
from signal_generator_core import generate_signals
from signal_generator_indicators import calculate_indicators_and_signal
from global_objects import global_trade_pool
from config_settings import get_backtest_settings
from redis_initializer import redis_client
from redis_client import get_json, set_json  # Импортируем функции напрямую
from bot_user_data import get_user_deposit, get_user_assets, add_user_trade

async def fetch_user_balance(exchange, user_id):
    """Запрашивает баланс пользователя и кэширует его в Redis"""
    balance_cache_key = f"balance:{user_id}"
    cached_balance = await get_json(balance_cache_key)  # Используем функцию get_json
    if cached_balance:
        logger_main.debug(f"Using cached balance for user {user_id}: {cached_balance}")
        return cached_balance
    try:
        balance = await exchange.fetch_balance()
        logger_main.debug(f"Fetched balance from exchange for user {user_id}: {balance}")
        total_deposit_usdt = 0.0
        assets = {}
        for asset, data in balance.items():
            if isinstance(data, dict) and 'free' in data and 'locked' in data:
                free = float(data['free']) if data['free'] else 0.0
                locked = float(data['locked']) if data['locked'] else 0.0
                total = free + locked
                assets[asset] = {'free': free, 'locked': locked, 'total': total}
                if asset == 'USDT':
                    total_deposit_usdt = total
                elif total > 0:
                    try:
                        ticker = await exchange.fetch_ticker(f"{asset}/USDT")
                        price = ticker['last'] if ticker and 'last' in ticker else 0
                        total_deposit_usdt += total * price
                    except Exception as e:
                        logger_main.warning(f"Cannot fetch price for {asset}/USDT: {str(e)}")
        balance_data = {'total_deposit_usdt': total_deposit_usdt, 'assets': assets}
        await set_json(balance_cache_key, balance_data, expire=300)  # Используем функцию set_json
        logger_main.info(f"Fetched balance for user {user_id}: {total_deposit_usdt} USDT")
        return balance_data
    except Exception as e:
        logger_main.error(f"Error fetching balance for user {user_id} from exchange: {str(e)}")
        # Используем депозит из bot_user_data.py как запасной вариант
        total_deposit_usdt = get_user_deposit(user_id)
        assets = get_user_assets(user_id)
        balance_data = {'total_deposit_usdt': total_deposit_usdt, 'assets': assets}
        logger_main.warning(f"Using fallback deposit from bot_user_data for user {user_id}: {total_deposit_usdt} USDT")
        return balance_data

async def execute_trade(exchange, symbol, side, user_id, trade_executor, confidence=0.5, market_conditions=None):
    """Выполняет торговую операцию на основе сигнала"""
    logger_main.info(f"Executing trade: {side} {symbol} for user {user_id} with confidence {confidence}")
    try:
        # Получаем текущую цену
        ticker = await exchange.fetch_ticker(symbol)
        if not ticker or 'last' not in ticker:
            logger_main.warning(f"Cannot fetch ticker for {symbol}")
            return None
        price = ticker['last']
        logger_main.debug(f"Fetched price for {symbol}: {price}")
        # Проверяем баланс перед выполнением сделки
        balance_data = await fetch_user_balance(exchange, user_id)
        if not balance_data:
            logger_main.warning(f"Cannot fetch balance for user {user_id}, skipping trade")
            return None
        total_deposit_usdt = balance_data['total_deposit_usdt']
        assets = balance_data['assets']
        logger_main.debug(f"User {user_id} balance: {total_deposit_usdt} USDT, assets: {assets}")
        MINIMUM_DEPOSIT = 10.0  # Минимальный депозит для торговли
        if total_deposit_usdt < MINIMUM_DEPOSIT:
            logger_main.warning(f"Insufficient deposit for user {user_id}: {total_deposit_usdt} USDT, required minimum {MINIMUM_DEPOSIT} USDT")
            return None
        # Проверяем наличие активов для продажи
        if side == 'sell':
            base_asset = symbol.split('/')[0]
            if base_asset not in assets or assets[base_asset]['total'] <= 0:
                logger_main.warning(f"Cannot sell {symbol}: user {user_id} has no {base_asset} available")
                return None
        # Формируем данные о сделке
        trade = {
            'user_id': user_id,
            'symbol': symbol,
            'side': side,
            'price': price,
            'timestamp': int(ticker['timestamp'] / 1000) if 'timestamp' in ticker else int(asyncio.get_event_loop().time()),
            'status': 'pending',
            'order_type': 'limit',
            'market_conditions': market_conditions or {}
        }
        logger_main.debug(f"Trade data prepared: {trade}")
        # Выполняем сделку через trade_executor
        order = await trade_executor.execute_trade(exchange, trade, confidence, market_conditions)
        logger_main.debug(f"trade_executor.execute_trade returned: {order}")
        if order:
            logger_main.info(f"Trade executed successfully: {order}")
            return order
        else:
            logger_main.warning(f"Failed to execute trade for {symbol}: trade_executor.execute_trade returned None")
            return None
    except Exception as e:
        logger_main.error(f"Error executing trade for {symbol}: {str(e)}")
        logger_exceptions.error(f"Error executing trade: {str(e)}", exc_info=True)
        return None

__all__ = ['execute_trade']
