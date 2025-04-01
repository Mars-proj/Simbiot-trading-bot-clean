from logging_setup import logger_main
from redis_client import RedisClient
from cache_utils import CacheUtils
from exchange_utils import fetch_ticker
from symbol_handler import validate_symbol
import time

class TradePool:
    def __init__(self, user_id, exchange_id):
        self.user_id = user_id
        self.exchange_id = exchange_id
        self.redis = RedisClient()
        self.cache = CacheUtils()

    async def add_trade(self, trade, exchange):
        """Adds a trade to the trade pool."""
        try:
            if not trade or 'symbol' not in trade:
                logger_main.error(f"Invalid trade data: {trade}")
                return False

            symbol = trade['symbol']
            if not await validate_symbol(self.exchange_id, self.user_id, symbol, testnet=exchange.testnet):
                logger_main.error(f"Invalid symbol in trade: {symbol}")
                return False

            trade['timestamp'] = int(time.time())
            key = f"trade:{self.user_id}:{self.exchange_id}:{trade['id']}"
            await self.redis.set(key, str(trade))
            logger_main.info(f"Added trade {trade['id']} for {symbol} to trade pool")
            return True
        except Exception as e:
            logger_main.error(f"Error adding trade to pool: {e}")
            return False

    async def get_trades(self, exchange):
        """Fetches all trades from the trade pool."""
        try:
            keys = await self.redis.keys(f"trade:{self.user_id}:{self.exchange_id}:*")
            trades = []
            for key in keys:
                trade_data = await self.redis.get(key)
                if trade_data:
                    trade = eval(trade_data)  # Safely evaluate the stringified dict
                    symbol = trade.get('symbol')
                    if not await validate_symbol(self.exchange_id, self.user_id, symbol, testnet=exchange.testnet):
                        logger_main.warning(f"Invalid symbol in trade: {symbol}, removing from pool")
                        await self.remove_trade(trade, exchange)
                        continue

                    # Fetch current price to update trade status
                    ticker = await fetch_ticker(exchange, symbol)
                    if ticker:
                        trade['current_price'] = ticker.get('last', 0)
                    trades.append(trade)

            logger_main.info(f"Fetched {len(trades)} trades from trade pool for user {self.user_id} on {self.exchange_id}")
            return trades
        except Exception as e:
            logger_main.error(f"Error fetching trades from pool: {e}")
            return None

    async def update_trade(self, trade, exchange):
        """Updates a trade in the trade pool."""
        try:
            if not trade or 'id' not in trade:
                logger_main.error(f"Invalid trade data for update: {trade}")
                return False

            key = f"trade:{self.user_id}:{self.exchange_id}:{trade['id']}"
            trade['timestamp'] = int(time.time())
            await self.redis.set(key, str(trade))
            logger_main.info(f"Updated trade {trade['id']} in trade pool")
            return True
        except Exception as e:
            logger_main.error(f"Error updating trade in pool: {e}")
            return False

    async def remove_trade(self, trade, exchange):
        """Removes a trade from the trade pool."""
        try:
            if not trade or 'id' not in trade:
                logger_main.error(f"Invalid trade data for removal: {trade}")
                return False

            key = f"trade:{self.user_id}:{self.exchange_id}:{trade['id']}"
            await self.redis.delete(key)
            logger_main.info(f"Removed trade {trade['id']} from trade pool")
            return True
        except Exception as e:
            logger_main.error(f"Error removing trade from pool: {e}")
            return False

    async def clear_trades(self, max_age_seconds=86400):
        """Clears outdated trades from the trade pool."""
        try:
            keys = await self.redis.keys(f"trade:{self.user_id}:{self.exchange_id}:*")
            current_time = int(time.time())
            removed = 0
            for key in keys:
                trade_data = await self.redis.get(key)
                if trade_data:
                    trade = eval(trade_data)
                    timestamp = trade.get('timestamp', 0)
                    if current_time - timestamp > max_age_seconds:
                        await self.redis.delete(key)
                        removed += 1
            logger_main.info(f"Cleared {removed} outdated trades from trade pool")
            return True
        except Exception as e:
            logger_main.error(f"Error clearing outdated trades: {e}")
            return False

__all__ = ['TradePool']
