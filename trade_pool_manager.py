import asyncio
from logging_setup import logger_main
from cache_utils import CacheUtils
from bot_user_data import BotUserData

async def schedule_trade_pool_cleanup(exchange_id, user_id, max_age_seconds=86400, interval=3600):
    """Schedules periodic cleanup of the trade pool."""
    cache = CacheUtils()
    while True:
        try:
            logger_main.info(f"Starting scheduled trade pool cleanup for user {user_id} on {exchange_id}")
            await cleanup_trade_pool(exchange_id, user_id, max_age_seconds)
            await sync_trades_to_user_cache(exchange_id, user_id)
            await asyncio.sleep(interval)
        except Exception as e:
            logger_main.error(f"Error in trade pool cleanup for user {user_id} on {exchange_id}: {e}")
            await asyncio.sleep(interval)

async def cleanup_trade_pool(exchange_id, user_id, max_age_seconds):
    """Cleans up outdated trades from the trade pool."""
    try:
        cache = CacheUtils()
        key = f"trade_pool:{exchange_id}:{user_id}"
        trades = await cache.get_list(key)
        if not trades:
            logger_main.debug(f"No trades to clean up for user {user_id} on {exchange_id}")
            return

        current_time = int(asyncio.get_event_loop().time())
        cutoff_time = current_time - max_age_seconds
        filtered_trades = [trade for trade in trades if trade['timestamp'] >= cutoff_time]

        # Update the trade pool
        await cache.redis.delete(key)
        for trade in filtered_trades:
            await cache.append_to_list(key, trade)
        logger_main.info(f"Cleared {len(trades) - len(filtered_trades)} outdated trades from trade pool")
    except Exception as e:
        logger_main.error(f"Error cleaning up trade pool for user {user_id} on {exchange_id}: {e}")

async def sync_trades_to_user_cache(exchange_id, user_id):
    """Synchronizes trades from the trade pool to the user cache."""
    try:
        cache = CacheUtils()
        trades = await cache.get_list(f"trade_pool:{exchange_id}:{user_id}")
        if not trades:
            logger_main.debug(f"No trades to sync for user {user_id} on {exchange_id}")
            return

        bot_user_data = BotUserData()
        for trade in trades:
            await bot_user_data.save_user_trade(user_id, trade)
        logger_main.info(f"Synced {len(trades)} trades to user cache for user {user_id} on {exchange_id}")
    except Exception as e:
        logger_main.error(f"Error syncing trades to user cache for user {user_id} on {exchange_id}: {e}")

__all__ = ['schedule_trade_pool_cleanup']
