from logging_setup import logger_main
from redis_client import RedisClient
from cache_utils import cache_symbol_data
from exchange_utils import fetch_ticker
from symbol_handler import validate_symbol

class TradePool:
    def __init__(self, user_id, exchange_id, volume_threshold=1000):
        self.user_id = user_id
        self.exchange_id = exchange_id
        self.redis = RedisClient()
        self.volume_threshold = volume_threshold

    async def add_trade(self, trade, exchange):
        """Adds a trade to the pool."""
        try:
            # Check for problematic symbols before caching
            symbol = trade.get('symbol')
            if not symbol:
                logger_main.error(f"Trade missing symbol: {trade}")
                return False

            # Validate symbol
            if not await validate_symbol(self.exchange_id, self.user_id, symbol):
                logger_main.error(f"Invalid symbol: {symbol}")
                return False

            # Fetch ticker to check volume
            ticker = await fetch_ticker(exchange, symbol, self.exchange_id, self.user_id)
            if not ticker or ticker.get('baseVolume', 0) < self.volume_threshold:
                logger_main.error(f"Symbol {symbol} has low volume: {ticker.get('baseVolume', 0)}")
                return False

            # Cache trade data
            await cache_symbol_data(symbol, trade)
            trade_key = f"trade:{self.user_id}:{self.exchange_id}:{trade['id']}"
            await self.redis.set(trade_key, trade)
            logger_main.info(f"Added trade {trade['id']} for user {self.user_id} on {self.exchange_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error adding trade for user {self.user_id} on {self.exchange_id}: {e}")
            return False

    async def get_trades(self, exchange):
        """Fetches all trades for the user."""
        try:
            trades = []
            trade_keys = await self.redis.keys(f"trade:{self.user_id}:{self.exchange_id}:*")
            for key in trade_keys:
                trade = await self.redis.get(key)
                if trade:
                    trades.append(trade)
            logger_main.info(f"Fetched {len(trades)} trades for user {self.user_id} on {self.exchange_id}")
            return trades
        except Exception as e:
            logger_main.error(f"Error fetching trades for user {self.user_id} on {self.exchange_id}: {e}")
            return None

    async def update_trade(self, trade, exchange):
        """Updates a trade in the pool."""
        try:
            trade_key = f"trade:{self.user_id}:{self.exchange_id}:{trade['id']}"
            await self.redis.set(trade_key, trade)
            logger_main.info(f"Updated trade {trade['id']} for user {self.user_id} on {self.exchange_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error updating trade {trade.get('id', 'N/A')} for user {self.user_id} on {self.exchange_id}: {e}")
            return False

    async def remove_trade(self, trade, exchange):
        """Removes a trade from the pool."""
        try:
            trade_key = f"trade:{self.user_id}:{self.exchange_id}:{trade['id']}"
            await self.redis.delete(trade_key)
            logger_main.info(f"Removed trade {trade['id']} for user {self.user_id} on {self.exchange_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error removing trade {trade.get('id', 'N/A')} for user {self.user_id} on {self.exchange_id}: {e}")
            return False

    async def clear_trades(self):
        """Clears all trades for the user from the pool."""
        try:
            trade_keys = await self.redis.keys(f"trade:{self.user_id}:{self.exchange_id}:*")
            for key in trade_keys:
                await self.redis.delete(key)
            logger_main.info(f"Cleared {len(trade_keys)} trades for user {self.user_id} on {self.exchange_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error clearing trades for user {self.user_id} on {self.exchange_id}: {e}")
            return False

__all__ = ['TradePool']
