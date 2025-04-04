# data_collector.py
import asyncio
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

        # Запрашиваем недавние сделки пользователя
        logger_main.debug(f"Fetching trades for user {user_id} on {exchange_id}")
        trades = await exchange.fetch_my_trades(symbol=None, since=None, limit=100)
        logger_main.debug(f"Fetched {len(trades)} trades for user {user_id} on {exchange_id}")

        if not trades:
            logger_main.warning(f"No trades found for user {user_id} on {exchange_id}")
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
