# check_all_trades.py
from logging_setup import logger_main
from trade_pool_core import TradePoolCore  # Заменили TradePool на TradePoolCore

async def check_all_trades(user_id, exchange_id):
    trade_pool = TradePoolCore(user_id, exchange_id)  # Заменили TradePool на TradePoolCore
    trades = await trade_pool.fetch_trades(exchange_id, user_id)
    logger_main.info(f"Checking all trades for user {user_id} on {exchange_id}: {len(trades)} trades found")
    return trades
