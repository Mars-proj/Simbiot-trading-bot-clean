# position_monitor.py
from logging_setup import logger_main
from trade_pool_core import TradePoolCore

async def monitor_positions(exchange_id, user_id, exchange, testnet=False):
    trade_pool = TradePoolCore()
    positions = await trade_pool.fetch_positions(exchange_id, user_id, exchange=exchange)
    if not positions:
        logger_main.info(f"No open positions for user {user_id} on {exchange_id}")
        return
    logger_main.info(f"Found {len(positions)} open positions for user {user_id} on {exchange_id}")
    # Здесь логика мониторинга позиций
