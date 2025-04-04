# trade_pool_core.py
from logging_setup import logger_main
from cache_utils import RedisClient

class TradePoolCore:
    def __init__(self):
        self.cache = RedisClient(f"redis://localhost:6379")

    async def fetch_trades(self, exchange_id, user_id):
        logger_main.info(f"Fetching trades from trade pool for user {user_id} on {exchange_id}")
        cache_key = f"user_trades:{user_id}"
        trades = self.cache.get_list(cache_key)
        if not trades:
            logger_main.warning(f"No trades found for user {user_id} on {exchange_id}")
            return []
        return trades

    async def fetch_positions(self, exchange_id, user_id, exchange=None):
        logger_main.info(f"Fetching positions for user {user_id} on {exchange_id}")
        cache_key = f"user_positions:{user_id}"
        cached_positions = self.cache.get_list(cache_key)
        if cached_positions:
            logger_main.info(f"Returning cached positions for {cache_key}: {len(cached_positions)} positions")
            return cached_positions

        if exchange is None:
            logger_main.error(f"No exchange provided to fetch positions for {exchange_id}:{user_id}")
            return []

        try:
            positions = await exchange.fetch_positions()
            self.cache.set_list(cache_key, positions)
            logger_main.info(f"Fetched {len(positions)} positions for user {user_id} on {exchange_id}")
            return positions
        except Exception as e:
            logger_main.error(f"Error fetching positions for {exchange_id}:{user_id}: {e}")
            return []
