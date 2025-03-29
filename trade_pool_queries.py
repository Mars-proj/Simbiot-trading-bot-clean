from logging_setup import logger_main
from utils import log_exception
from trade_pool_redis import get_all_trades_from_redis, get_recent_trades_from_redis
from trade_pool_tokens import update_available_tokens, get_available_tokens
from redis_initializer import redis_client

async def get_all_trades(self, source=None):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    redis_client = await self._ensure_redis_client()
    return await get_all_trades_from_redis(redis_client, self.trade_key_prefix, source)

async def get_trades_by_user(self, user_id, source=None):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    try:
        user_cache = await self._get_user_cache(user_id)
        user_trades = await user_cache.get_trades()
        if source:
            user_trades = [trade for trade in user_trades if trade.get('source') == source]
        return user_trades
    except Exception as e:
        logger_main.error(f"Error fetching trades for user {user_id}: {str(e)}")
        log_exception(f"Error fetching user trades: {str(e)}", e)
        return []

async def get_user_summary(self, user_id):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    try:
        user_cache = await self._get_user_cache(user_id)
        return await user_cache.get_summary()
    except Exception as e:
        logger_main.error(f"Error fetching summary for user {user_id}: {str(e)}")
        log_exception(f"Error fetching user summary: {str(e)}", e)
        return {
            "deposit": 0.0,
            "trade_count": 0,
            "pnl": 0.0,
            "profit": 0.0,
            "loss": 0.0,
            "signals": {},
            "pairs": {}
        }

async def get_trades_by_symbol(self, symbol, source=None):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    try:
        trades = await self.get_all_trades(source=source)
        return [trade for trade in trades if trade.get('symbol') == symbol]
    except Exception as e:
        logger_main.error(f"Error fetching trades for symbol {symbol}: {str(e)}")
        log_exception(f"Error fetching symbol trades: {str(e)}", e)
        return []

async def get_recent_trades(self, limit=1000):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    redis_client = await self._ensure_redis_client()
    return await get_recent_trades_from_redis(redis_client, self.max_recent_trades, limit)

async def update_available_tokens(self, user_id, tokens):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    await update_available_tokens(user_id, tokens, self.ttl_seconds, self.available_tokens_key_prefix)

async def get_available_tokens(self, user_id):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    return await get_available_tokens(user_id, self.available_tokens_key_prefix)

async def close(self):
    if redis_client is None:
        logger_main.error("redis_client is not initialized")
        raise ValueError("redis_client is not initialized")
    logger_main.info("Closing Redis connection in trade_pool.py")
    try:
        if self._redis_client is not None:
            await self._redis_client.close()
            self._redis_client = None
    except Exception as e:
        logger_main.error(f"Error closing Redis connection: {str(e)}")
        log_exception(f"Error closing Redis: {str(e)}", e)

__all__ = ['get_all_trades', 'get_trades_by_user', 'get_user_summary', 'get_trades_by_symbol', 'get_recent_trades', 'update_available_tokens', 'get_available_tokens', 'close']
