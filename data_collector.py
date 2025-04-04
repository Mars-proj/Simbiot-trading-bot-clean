# data_collector.py
import asyncio
import time
import traceback
from logging_setup import logger_main
from exchange_pool import ExchangePool

async def collect_training_data(exchange_id, user_id, testnet=False):
    """
    Collects training data (e.g., recent trades) for the given user and exchange.
    Args:
        exchange_id (str): Exchange identifier (e.g., 'mexc')
        user_id (str): User identifier
        testnet (bool): Whether to use testnet
    Returns:
        list: List of trade data entries
    """
    try:
        logger_main.info(f"Collecting training data for user {user_id} on {exchange_id}")
        
        # Получаем экземпляр биржи из ExchangePool
        exchange_pool = ExchangePool()
        exchange = await exchange_pool.get_exchange(exchange_id, user_id, testnet)
        if not exchange:
            logger_main.error(f"Failed to get exchange instance for {exchange_id}:{user_id}")
            return []

        # Пробуем получить недавние сделки пользователя для BTCUSDT
        symbol = "BTCUSDT"  # Указываем конкретный символ
        logger_main.debug(f"Fetching user trades for user {user_id} on {exchange_id} for symbol {symbol}")
        since = int((time.time() - 30*24*60*60) * 1000)  # Последние 30 дней в миллисекундах
        logger_main.debug(f"Calling fetch_my_trades with symbol={symbol}, since={since}, limit=100")
        trades = await exchange.fetch_my_trades(symbol=symbol, since=since, limit=100)
        logger_main.debug(f"Fetched {len(trades)} user trades for user {user_id} on {exchange_id}: {trades[:5] if trades else '[]'}")

        # Если сделки пользователя не найдены, пробуем получить исторические сделки для BTCUSDT
        if not trades:
            logger_main.warning(f"No user trades found for user {user_id} on {exchange_id}, falling back to historical trades for {symbol}")
            try:
                logger_main.debug(f"Calling fetch_trades for {symbol} with since={since}, limit=100")
                historical_trades = await exchange.fetch_trades(symbol=symbol, since=since, limit=100)
                logger_main.debug(f"Fetched {len(historical_trades)} historical trades for {symbol} on {exchange_id}: {historical_trades[:5] if historical_trades else '[]'}")
                trades = historical_trades
            except Exception as e:
                logger_main.error(f"Failed to fetch historical trades for {symbol} on {exchange_id}: {e}\n{traceback.format_exc()}")
                return []

        if not trades:
            logger_main.warning(f"No trades (user or historical) found for user {user_id} on {exchange_id}")
            return []

        # Форматируем данные о сделках
        trade_data = []
        for trade in trades:
            trade_entry = {
                'price': trade['price'],
                'amount': trade['amount'],
                'timestamp': trade['timestamp'],
                'side': trade['side'],
                'symbol': trade['symbol']
            }
            trade_data.append(trade_entry)

        logger_main.info(f"Collected {len(trade_data)} trade entries for user {user_id} on {exchange_id}")
        return trade_data

    except Exception as e:
        logger_main.error(f"Error collecting training data for user {user_id} on {exchange_id}: {e}\n{traceback.format_exc()}")
        return []
