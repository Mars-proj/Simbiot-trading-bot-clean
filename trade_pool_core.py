from logging_setup import logger_main
from redis_client import RedisClient
from cache_utils import CacheUtils
from exchange_utils import fetch_ticker
from symbol_handler import validate_symbol
import time
import json

class TradePool:
    def __init__(self, user_id, exchange_id):
        self.user_id = user_id
        self.exchange_id = exchange_id
        self.redis = RedisClient()
        self.cache = CacheUtils()
        self.trade_key = f"trades:{user_id}:{exchange_id}"

    async def add_trade(self, trade, exchange):
        """Adds a trade to the pool."""
        try:
            if not trade or 'symbol' not in trade:
                logger_main.error(f"Invalid trade data: {trade}")
                return False

            symbol = trade['symbol']
            if not await validate_symbol(self.exchange_id, self.user_id, symbol, testnet=exchange.testnet):
                logger_main.error(f"Invalid symbol: {symbol}")
                return False

            trades = await self.get_trades(exchange)
            trades.append(trade)
            await self.redis.set(self.trade_key, json.dumps(trades))
            logger_main.info(f"Added trade for {symbol} to pool for user {self.user_id} on {self.exchange_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error adding trade to pool for user {self.user_id} on {self.exchange_id}: {e}")
            return False

    async def get_trades(self, exchange):
        """Gets all trades from the pool, removes outdated trades."""
        try:
            trades_data = await self.redis.get(self.trade_key)
            trades = json.loads(trades_data) if trades_data else []

            # Remove outdated trades (older than 24 hours)
            current_time = int(time.time() * 1000)  # Current time in milliseconds
            max_age = 24 * 60 * 60 * 1000  # 24 hours in milliseconds
            updated_trades = []
            for trade in trades:
                trade_timestamp = trade.get('timestamp', 0)
                trade_age = current_time - trade_timestamp
                if trade_age <= max_age:
                    updated_trades.append(trade)
                else:
                    logger_main.info(f"Removed outdated trade for {trade.get('symbol', 'N/A')} from pool for user {self.user_id} on {self.exchange_id}")

            if len(updated_trades) != len(trades):
                await self.redis.set(self.trade_key, json.dumps(updated_trades))

            return updated_trades
        except Exception as e:
            logger_main.error(f"Error getting trades from pool for user {self.user_id} on {self.exchange_id}: {e}")
            return []

    async def remove_trade(self, trade, exchange):
        """Removes a trade from the pool."""
        try:
            trades = await self.get_trades(exchange)
            trades = [t for t in trades if t != trade]
            await self.redis.set(self.trade_key, json.dumps(trades))
            logger_main.info(f"Removed trade for {trade.get('symbol', 'N/A')} from pool for user {self.user_id} on {self.exchange_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error removing trade from pool for user {self.user_id} on {self.exchange_id}: {e}")
            return False

    async def update_trade(self, trade, exchange):
        """Updates a trade in the pool."""
        try:
            trades = await self.get_trades(exchange)
            for i, t in enumerate(trades):
                if t['id'] == trade['id']:
                    trades[i] = trade
                    break
            await self.redis.set(self.trade_key, json.dumps(trades))
            logger_main.info(f"Updated trade for {trade.get('symbol', 'N/A')} in pool for user {self.user_id} on {self.exchange_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error updating trade in pool for user {self.user_id} on {self.exchange_id}: {e}")
            return False

    async def clear_trades(self):
        """Clears all trades from the pool."""
        try:
            await self.redis.delete(self.trade_key)
            logger_main.info(f"Cleared all trades from pool for user {self.user_id} on {self.exchange_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error clearing trades from pool for user {self.user_id} on {self.exchange_id}: {e}")
            return False

__all__ = ['TradePool']
