import redis.asyncio as redis
import uuid
import asyncio
from logging_setup import logger_main, logger_trade_pool
from utils import log_exception
from json_handler import dumps, loads

async def add_trade_to_redis(redis_client, trade_data, trade_id, ttl_seconds, max_recent_trades):
    """Adds a trade to Redis"""
    start_time = asyncio.get_event_loop().time()
    logger_main.info(f"Saving trade to Redis: key {trade_id}")
    await redis_client.setex(trade_id, ttl_seconds, dumps(trade_data))  # Store for 7 days
    logger_trade_pool.info(f"Trade added to Redis: {trade_id} - {trade_data}")
    # Save to buffer for online learning
    recent_trades_key = "recent_trades"
    trade_index_key = f"trade_index:{trade_id}"  # Index for quick lookup
    await redis_client.hset("trade_indices", trade_id, recent_trades_key)  # Store index
    await redis_client.lpush(recent_trades_key, dumps(trade_data))
    # Limit buffer size
    await redis_client.ltrim(recent_trades_key, 0, max_recent_trades - 1)
    logger_main.info(f"Trade added to recent_trades buffer: {trade_id}")
    duration = asyncio.get_event_loop().time() - start_time
    logger_main.info(f"Trade {trade_id} added to Redis in {duration:.2f} seconds")

async def update_trade_pnl_in_redis(redis_client, trade_id, pnl, status, ttl_seconds, max_recent_trades):
    """Updates PNL and status of a trade in Redis"""
    start_time = asyncio.get_event_loop().time()
    trade_data = await redis_client.get(trade_id)
    if not trade_data:
        logger_main.error(f"Trade {trade_id} not found in Redis")
        return False
    trade = loads(trade_data)
    trade["pnl"] = float(pnl)
    trade["status"] = status
    # Update in Redis (main pool)
    await redis_client.setex(trade_id, ttl_seconds, dumps(trade))
    logger_trade_pool.info(f"Trade updated in Redis: {trade_id} - PNL={pnl}, status={status}")
    # Update in recent_trades buffer using index
    recent_trades_key = "recent_trades"
    trade_index = await redis_client.hget("trade_indices", trade_id)
    if trade_index:
        trades = await redis_client.lrange(recent_trades_key, 0, max_recent_trades - 1)
        for i, trade_json in enumerate(trades):
            recent_trade = loads(trade_json)
            if recent_trade["trade_id"] == trade_id:
                recent_trade["pnl"] = float(pnl)
                recent_trade["status"] = status
                await redis_client.lset(recent_trades_key, i, dumps(recent_trade))
                break
        logger_main.info(f"Trade {trade_id} updated in recent_trades buffer")
    duration = asyncio.get_event_loop().time() - start_time
    logger_main.info(f"Trade {trade_id} updated in Redis in {duration:.2f} seconds")
    return True

async def get_all_trades_from_redis(redis_client, trade_key_prefix, source=None):
    """Gets all trades from Redis with optional source filtering"""
    logger_main.info(f"Starting to fetch all trades from TradePool (source={source})")
    try:
        trades = []
        cursor = "0"
        start_time = asyncio.get_event_loop().time()
        while True:
            cursor, keys = await redis_client.scan(cursor=cursor, match=f"{trade_key_prefix}*")
            for key in keys:
                trade_data = await redis_client.get(key)
                if trade_data:
                    trade = loads(trade_data)
                    if source is None or trade.get('source') == source:
                        trades.append(trade)
            if cursor == "0":
                break
        duration = asyncio.get_event_loop().time() - start_time
        logger_main.info(f"Fetched {len(trades)} trades from TradePool (source={source}) in {duration:.2f} seconds")
        return trades
    except Exception as e:
        logger_main.error(f"Error fetching trades from TradePool: {str(e)}")
        log_exception(f"Error fetching trades: {str(e)}", e)
        return []

async def get_recent_trades_from_redis(redis_client, max_recent_trades, limit=1000):
    """Returns the most recent trades from Redis (up to the specified limit)"""
    logger_trade_pool.info(f"Fetching the last {limit} trades from the pool")
    try:
        recent_trades_key = "recent_trades"
        start_time = asyncio.get_event_loop().time()
        trade_jsons = await redis_client.lrange(recent_trades_key, 0, limit - 1)
        trades = [loads(trade_json) for trade_json in trade_jsons]
        # Sort by timestamp (in case Redis order is not guaranteed)
        sorted_trades = sorted(trades, key=lambda x: x.get('timestamp', 0), reverse=True)
        duration = asyncio.get_event_loop().time() - start_time
        logger_trade_pool.info(f"Fetched {len(sorted_trades)} recent trades from Redis in {duration:.2f} seconds")
        return sorted_trades
    except Exception as e:
        logger_main.error(f"Error fetching recent trades: {str(e)}")
        log_exception(f"Error fetching recent trades: {str(e)}", e)
        return []

__all__ = [
    'add_trade_to_redis',
    'update_trade_pnl_in_redis',
    'get_all_trades_from_redis',
    'get_recent_trades_from_redis'
]
