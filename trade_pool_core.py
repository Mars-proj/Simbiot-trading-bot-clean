import redis.asyncio as redis
import uuid
import json
from logging_setup import logger_main
from logging_setup import logger_exceptions
from trade_pool_redis import add_trade_to_redis, update_trade_pnl_in_redis
from trade_pool_file import add_trade_to_files, update_trade_pnl_in_files
from user_trade_cache import UserTradeCache

# Определяем настройки логирования прямо здесь
LOGGING_SETTINGS = {
    'trade_pool_log_file': '/root/trading_bot/trade_pool.log'
}

class TradePool:
    def __init__(self):
        self._redis_client = None  # Lazy initialization
        self.trade_key_prefix = "trade:"
        self.available_tokens_key_prefix = "available_tokens:"
        self.log_file = LOGGING_SETTINGS['trade_pool_log_file']
        self.json_file = "/root/trading_bot/trades.json"
        self.max_recent_trades = 10000
        self.ttl_seconds = 604800  # 7 days in seconds
        self.user_caches = {}  # Dictionary to store UserTradeCache instances for each user

    async def _ensure_redis_client(self):
        """Initializes Redis client if not already created"""
        if self._redis_client is None:
            logger_main.info("Creating Redis client in trade_pool.py")
            self._redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            logger_main.info("Checking Redis connection")
            try:
                ping_result = await self._redis_client.ping()
                logger_main.info(f"Connection check result: {ping_result}")
                if not ping_result:
                    raise Exception("Failed to connect to Redis")
                logger_main.info("Redis client successfully initialized in trade_pool.py")
            except Exception as e:
                logger_main.error(f"Error initializing Redis client: {str(e)}")
                logger_exceptions.error(f"Error initializing Redis: {str(e)}", exc_info=True)
                raise
        return self._redis_client

    async def _get_user_cache(self, user_id):
        """Returns the UserTradeCache instance for the given user"""
        if user_id not in self.user_caches:
            self.user_caches[user_id] = UserTradeCache(user_id, max_trades=self.max_recent_trades, ttl_seconds=self.ttl_seconds)
        return self.user_caches[user_id]

    async def add_trade(self, trade_data):
        """Adds a trade to the pool and user's cache"""
        logger_main.info("Starting TradePool add_trade")
        if not isinstance(trade_data, dict):
            logger_main.error("trade_data must be a dictionary")
            return

        # Add additional fields with default values
        trade_data["user_id"] = trade_data.get("user_id", "")
        trade_data["signals"] = trade_data.get("signals", {
            "signal_generator": 0,
            "strategy_signals": {},
            "combined_signal": 0
        })
        trade_data["signal_metrics"] = trade_data.get("signal_metrics", {})
        trade_data["market_conditions"] = trade_data.get("market_conditions", {})
        trade_data["pnl"] = trade_data.get("pnl", 0.0)
        trade_data["status"] = trade_data.get("status", "pending")
        trade_data["related_trade_id"] = trade_data.get("related_trade_id", None)
        trade_data["source"] = trade_data.get("source", "real")

        # Create trade_id using UUID for uniqueness
        trade_id = f"trade:{uuid.uuid4()}"
        trade_data["trade_id"] = trade_id

        # Log added fields at INFO level
        logger_main.info(f"Added fields to trade_data: user_id={trade_data['user_id']}, "
                         f"signals={trade_data['signals']}, "
                         f"signal_metrics={trade_data['signal_metrics']}, "
                         f"market_conditions={trade_data['market_conditions']}, "
                         f"pnl={trade_data['pnl']}, "
                         f"status={trade_data['status']}, "
                         f"related_trade_id={trade_data['related_trade_id']}, "
                         f"trade_id={trade_data['trade_id']}, "
                         f"source={trade_data['source']}")

        try:
            redis_client = await self._ensure_redis_client()
            # Add to Redis (global pool)
            add_trade_to_redis(redis_client, trade_data, trade_id, self.ttl_seconds, self.max_recent_trades)
            # Add to files
            add_trade_to_files(trade_data, trade_id, self.log_file, self.json_file)
            # Add to user's cache
            if trade_data["user_id"]:
                user_cache = await self._get_user_cache(trade_data["user_id"])
                await user_cache.add_trade(trade_data)
        except Exception as e:
            logger_main.error(f"Error adding trade to pool: {str(e)}")
            logger_exceptions.error(f"Error adding trade: {str(e)}", exc_info=True)

    async def get_all_trades(self):
        """Retrieves all trades from Redis"""
        try:
            redis_client = await self._ensure_redis_client()
            keys = await redis_client.keys(f"{self.trade_key_prefix}*")
            trades = []
            for key in keys:
                trade_data = await redis_client.get(key)
                if trade_data:
                    trade = json.loads(trade_data)
                    trades.append(trade)
            return trades
        except Exception as e:
            logger_main.error(f"Error retrieving trades: {str(e)}")
            logger_exceptions.error(f"Error retrieving trades: {str(e)}", exc_info=True)
            return []

    async def update_trade_pnl(self, trade_id, pnl, status="completed"):
        """Updates PNL and status of a trade"""
        logger_main.info(f"Updating PNL for trade {trade_id}: PNL={pnl}, status={status}")
        try:
            redis_client = await self._ensure_redis_client()
            # Update in Redis (global pool)
            success = await update_trade_pnl_in_redis(redis_client, trade_id, pnl, status, self.ttl_seconds, self.max_recent_trades)
            if not success:
                return False
            # Update in files
            update_trade_pnl_in_files(trade_id, pnl, status, self.log_file, self.json_file)
            # Update in user's cache (if applicable)
            trade_data = await redis_client.get(trade_id)
            if trade_data:
                trade = json.loads(trade_data)
                user_id = trade.get("user_id")
                if user_id:
                    user_cache = await self._get_user_cache(user_id)
                    trade["pnl"] = float(pnl)
                    trade["status"] = status
                    await user_cache.update_summary(trade)
            return True
        except Exception as e:
            logger_main.error(f"Error updating PNL for trade {trade_id}: {str(e)}")
            logger_exceptions.error(f"Error updating PNL: {str(e)}", exc_info=True)
            return False

__all__ = ['TradePool']
