import asyncio
from logging_setup import logger_main
from trade_pool_core import TradePool

async def schedule_trade_pool_cleanup(exchange_id, user_id, max_age_seconds=86400, interval=3600):
    """Schedules periodic cleanup of outdated trades in the trade pool."""
    try:
        trade_pool = TradePool(user_id, exchange_id)
        while True:
            logger_main.info(f"Starting scheduled trade pool cleanup for user {user_id} on {exchange_id}")
            await trade_pool.clear_trades(max_age_seconds=max_age_seconds)
            await asyncio.sleep(interval)  # Run cleanup every hour by default
    except Exception as e:
        logger_main.error(f"Error in trade pool cleanup schedule for user {user_id} on {exchange_id}: {e}")
        return False

__all__ = ['schedule_trade_pool_cleanup']
