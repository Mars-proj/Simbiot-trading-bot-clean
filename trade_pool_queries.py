import ccxt.async_support as ccxt
import asyncio
from logging_setup import logger_main
from redis_client import redis_client

async def get_all_trades(exchange, user_id, cache_ttl=3600):
    """Fetches all trades for a user from Redis or the exchange."""
    try:
        # Try to fetch from Redis
        key = f"trades:{user_id}:{exchange.id}"
        trades = await redis_client.get(key)
        if trades is not None:
            if not isinstance(trades, list):
                logger_main.error(f"Invalid trade data format in Redis for key {key}: {type(trades)}")
                trades = []
            else:
                logger_main.info(f"Fetched {len(trades)} trades for user {user_id} from Redis")
                return trades

        # If not in Redis, fetch from exchange
        trades = await exchange.fetch_my_trades()
        if trades is None:
            logger_main.error(f"Failed to fetch trades from {exchange.id} for user {user_id}")
            return []

        if trades:
            # Store in Redis
            await redis_client.set(key, trades, ex=cache_ttl)
            logger_main.info(f"Fetched {len(trades)} trades for user {user_id} from {exchange.id} and cached in Redis for {cache_ttl} seconds")
        else:
            logger_main.warning(f"No trades found for user {user_id} on {exchange.id}")
        return trades
    except Exception as e:
        logger_main.error(f"Error fetching trades for user {user_id} on {exchange.id}: {e}")
        return []

async def save_trade(user_id, exchange_id, trade, cache_ttl=3600):
    """Saves a trade to Redis."""
    try:
        key = f"trades:{user_id}:{exchange_id}"
        trades = await redis_client.get(key)
        if trades is not None:
            if not isinstance(trades, list):
                logger_main.error(f"Invalid trade data format in Redis for key {key}: {type(trades)}")
                trades = []
            else:
                trades.append(trade)
        else:
            trades = [trade]
        await redis_client.set(key, trades, ex=cache_ttl)
        logger_main.info(f"Saved trade for user {user_id} on {exchange_id} to Redis for {cache_ttl} seconds")
    except Exception as e:
        logger_main.error(f"Error saving trade for user {user_id} on {exchange_id}: {e}")

__all__ = ['get_all_trades', 'save_trade']
