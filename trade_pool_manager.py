from logging_setup import logger_main
from trade_pool_core import TradePool
from config_keys import SUPPORTED_EXCHANGES
import time
import asyncio

async def manage_trade_pool(exchange_id, user_id, max_age_seconds=86400):
    """Manages the trade pool for a user by cleaning up outdated trades."""
    try:
        # Validate inputs
        if exchange_id not in SUPPORTED_EXCHANGES:
            logger_main.error(f"Exchange {exchange_id} not supported")
            return False
        if not user_id or not isinstance(user_id, str):
            logger_main.error(f"Invalid user_id: {user_id}")
            return False

        # Initialize trade pool
        trade_pool = TradePool(user_id, exchange_id)

        # Fetch all trades
        trades = await trade_pool.get_trades(None)  # No exchange needed for Redis fetch
        if trades is None:
            logger_main.error(f"Failed to fetch trades for user {user_id} on {exchange_id}")
            return False

        # Check for outdated trades
        current_time = int(time.time() * 1000)  # Current time in milliseconds
        outdated_trades = []
        for trade in trades:
            trade_timestamp = trade.get('timestamp', 0)
            trade_age = (current_time - trade_timestamp) / 1000  # Age in seconds
            if trade_age > max_age_seconds:
                outdated_trades.append(trade)

        # Remove outdated trades
        for trade in outdated_trades:
            await trade_pool.remove_trade(trade, None)  # No exchange needed for Redis delete

        logger_main.info(f"Managed trade pool for user {user_id} on {exchange_id}: removed {len(outdated_trades)} outdated trades")
        return True
    except Exception as e:
        logger_main.error(f"Error managing trade pool for user {user_id} on {exchange_id}: {e}")
        return False

async def schedule_trade_pool_cleanup(exchange_id, user_id, max_age_seconds=86400, interval=3600):
    """Schedules periodic cleanup of the trade pool."""
    try:
        while True:
            logger_main.info(f"Starting scheduled trade pool cleanup for user {user_id} on {exchange_id}")
            await manage_trade_pool(exchange_id, user_id, max_age_seconds)
            await asyncio.sleep(interval)  # Run every hour by default
    except Exception as e:
        logger_main.error(f"Error in scheduled trade pool cleanup for user {user_id} on {exchange_id}: {e}")
        return False

__all__ = ['manage_trade_pool', 'schedule_trade_pool_cleanup']
