import asyncio
from logging_setup import logger_main
from trade_pool_queries import get_all_trades, save_trade

class TradePool:
    """Manages a pool of trades with support for different storage methods, filtering, transfers, and caching."""
    def __init__(self, user_id, exchange_id, storage_method='redis'):
        self.user_id = user_id
        self.exchange_id = exchange_id
        self.storage_method = storage_method  # 'redis' or 'file'
        self.cache = {}  # In-memory cache for quick access

    async def add_trade(self, trade, token=None):
        """Adds a trade to the pool, optionally filtering by token."""
        try:
            # Check if the symbol is problematic (e.g., low volume)
            symbol = trade.get('symbol')
            if symbol:
                # Placeholder for volume check (should be fetched from exchange or cache)
                volume = 500  # Example: Assume low volume
                if volume < 1000:
                    logger_main.warning(f"Symbol {symbol} has low volume ({volume}), not caching")
                    return False

            if token and trade.get('symbol') != token:
                logger_main.info(f"Trade for {trade.get('symbol')} does not match token {token}, skipping")
                return False
            await save_trade(self.user_id, self.exchange_id, trade)
            # Update cache
            key = f"{self.user_id}:{self.exchange_id}"
            if key not in self.cache:
                self.cache[key] = []
            self.cache[key].append(trade)
            logger_main.info(f"Added trade for user {self.user_id} on {self.exchange_id} and cached")
            return True
        except Exception as e:
            logger_main.error(f"Error adding trade for user {self.user_id} on {self.exchange_id}: {e}")
            return False

    async def get_trades(self, exchange, token=None):
        """Fetches trades from the pool, optionally filtering by token."""
        try:
            # Check cache first
            key = f"{self.user_id}:{self.exchange_id}"
            if key in self.cache:
                trades = self.cache[key]
                logger_main.info(f"Fetched {len(trades)} trades from cache for user {self.user_id} on {self.exchange_id}")
            else:
                trades = await get_all_trades(exchange, self.user_id)
                self.cache[key] = trades

            if token:
                trades = [trade for trade in trades if trade.get('symbol') == token]
            logger_main.info(f"Fetched {len(trades)} trades for user {self.user_id} on {self.exchange_id}" + (f" for token {token}" if token else ""))
            return trades
        except Exception as e:
            logger_main.error(f"Error fetching trades for user {self.user_id} on {self.exchange_id}: {e}")
            return []

    async def transfer_trade(self, trade, target_user_id):
        """Transfers a trade to another user's pool."""
        try:
            await save_trade(target_user_id, self.exchange_id, trade)
            # Update cache for target user
            target_key = f"{target_user_id}:{self.exchange_id}"
            if target_key not in self.cache:
                self.cache[target_key] = []
            self.cache[target_key].append(trade)
            logger_main.info(f"Transferred trade from user {self.user_id} to {target_user_id} on {self.exchange_id}")
            return True
        except Exception as e:
            logger_main.error(f"Error transferring trade from user {self.user_id} to {target_user_id} on {self.exchange_id}: {e}")
            return False

__all__ = ['TradePool']
