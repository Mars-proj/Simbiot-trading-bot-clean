import asyncio
from redis_initializer import redis_client
from logging_setup import logger_main
from utils import log_exception
from json_handler import dumps, loads

class UserTradeCache:
    def __init__(self, user_id, max_trades=1000, ttl_seconds=604800):
        self.user_id = user_id
        self.max_trades = max_trades
        self.ttl_seconds = ttl_seconds
        self.cache_key = f"user_trades:{user_id}"
        self.summary_key = f"user_summary:{user_id}"
        if redis_client is None:
            logger_main.error("redis_client is not initialized")
            raise ValueError("redis_client is not initialized")

    async def add_trade(self, trade_data):
        try:
            trade_json = dumps(trade_data)
            await redis_client.lpush(self.cache_key, trade_json)
            await redis_client.ltrim(self.cache_key, 0, self.max_trades - 1)
            await redis_client.expire(self.cache_key, self.ttl_seconds)
            await self.update_summary(trade_data)
        except Exception as e:
            logger_main.error(f"Error adding trade to cache for user {self.user_id}: {str(e)}")
            log_exception(f"Error adding trade to cache: {str(e)}", e)

    async def update_summary(self, trade_data):
        try:
            summary_data = await redis_client.get(self.summary_key)
            summary = loads(summary_data) if summary_data else {
                "deposit": 0.0,
                "trade_count": 0,
                "pnl": 0.0,
                "profit": 0.0,
                "loss": 0.0,
                "signals": {},
                "pairs": {}
            }
            summary["trade_count"] += 1
            trade_pnl = trade_data.get("pnl", 0.0)
            summary["pnl"] += trade_pnl
            if trade_pnl > 0:
                summary["profit"] += trade_pnl
            else:
                summary["loss"] += abs(trade_pnl)
            signal = trade_data.get("signals", {}).get("combined_signal", "unknown")
            pair = trade_data.get("symbol", "unknown")
            summary["signals"][signal] = summary["signals"].get(signal, 0) + 1
            summary["pairs"][pair] = summary["pairs"].get(pair, 0) + 1
            if "deposit" in trade_data:
                summary["deposit"] = trade_data["deposit"]
            await redis_client.setex(self.summary_key, self.ttl_seconds, dumps(summary))
        except Exception as e:
            logger_main.error(f"Error updating summary for user {self.user_id}: {str(e)}")
            log_exception(f"Error updating summary: {str(e)}", e)

    async def get_summary(self):
        try:
            summary_data = await redis_client.get(self.summary_key)
            return loads(summary_data) if summary_data else {
                "deposit": 0.0,
                "trade_count": 0,
                "pnl": 0.0,
                "profit": 0.0,
                "loss": 0.0,
                "signals": {},
                "pairs": {}
            }
        except Exception as e:
            logger_main.error(f"Error fetching summary for user {self.user_id}: {str(e)}")
            log_exception(f"Error fetching summary: {str(e)}", e)
            return {
                "deposit": 0.0,
                "trade_count": 0,
                "pnl": 0.0,
                "profit": 0.0,
                "loss": 0.0,
                "signals": {},
                "pairs": {}
            }

    async def get_trades(self, limit=1000):
        try:
            trade_jsons = await redis_client.lrange(self.cache_key, 0, limit - 1)
            return [loads(trade_json) for trade_json in trade_jsons]
        except Exception as e:
            logger_main.error(f"Error fetching trades for user {self.user_id}: {str(e)}")
            log_exception(f"Error fetching trades: {str(e)}", e)
            return []

__all__ = ['UserTradeCache']
