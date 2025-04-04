# trade_pool_manager.py
import asyncio
from logging_setup import logger_main
from cache_utils import RedisClient  # Заменили CacheUtils на RedisClient

async def schedule_trade_pool_cleanup(exchange_id, user_id, max_age_seconds, interval):
    cache = RedisClient(f"redis://localhost:6379")  # Заменили CacheUtils на RedisClient
    while True:
        try:
            logger_main.info(f"Cleaning up trade pool for {exchange_id}:{user_id}")
            cache_key = f"user_trades:{user_id}"
            trades = cache.get_list(cache_key)
            if trades:
                # Здесь логика очистки
                pass
        except Exception as e:
            logger_main.error(f"Error cleaning up trade pool: {e}")
        await asyncio.sleep(interval)

async def cleanup_old_trades(exchange_id, user_id, max_age_seconds):
    cache = RedisClient(f"redis://localhost:6379")  # Заменили CacheUtils на RedisClient
    try:
        logger_main.info(f"Cleaning up old trades for {exchange_id}:{user_id}")
        cache_key = f"user_trades:{user_id}"
        trades = cache.get_list(cache_key)
        if trades:
            # Здесь логика удаления старых сделок
            pass
    except Exception as e:
        logger_main.error(f"Error cleaning up old trades: {e}")

async def remove_expired_trades(exchange_id, user_id, max_age_seconds):
    cache = RedisClient(f"redis://localhost:6379")  # Заменили CacheUtils на RedisClient
    try:
        logger_main.info(f"Removing expired trades for {exchange_id}:{user_id}")
        cache_key = f"user_trades:{user_id}"
        trades = cache.get_list(cache_key)
        if trades:
            # Здесь логика удаления просроченных сделок
            pass
    except Exception as e:
        logger_main.error(f"Error removing expired trades: {e}")
